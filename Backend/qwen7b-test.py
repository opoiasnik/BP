"""A simple command-line interactive chat demo for Qwen2.5-Instruct model with left-padding using bos_token."""

import argparse
import os
import platform
import shutil
from copy import deepcopy
from threading import Thread

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from transformers.trainer_utils import set_seed

DEFAULT_CKPT_PATH = "Qwen/Qwen2.5-7B-Instruct"

_WELCOME_MSG = """\
Welcome to use Qwen2.5-Instruct model, type text to start chat, type :h to show command help.
"""
_HELP_MSG = """\
Commands:
    :help / :h              Show this help message              
    :exit / :quit / :q      Exit the demo                       
    :clear / :cl            Clear screen                        
    :clear-history / :clh   Clear history                       
    :history / :his         Show history                        
    :seed                   Show current random seed            
    :seed <N>               Set random seed to <N>              
    :conf                   Show current generation config      
    :conf <key>=<value>     Change generation config            
    :reset-conf             Reset generation config             
"""

_ALL_COMMAND_NAMES = [
    "help",
    "h",
    "exit",
    "quit",
    "q",
    "clear",
    "cl",
    "clear-history",
    "clh",
    "history",
    "his",
    "seed",
    "conf",
    "reset-conf",
]


def _setup_readline():
    try:
        import readline
    except ImportError:
        return

    _matches = []

    def _completer(text, state):
        nonlocal _matches

        if state == 0:
            _matches = [
                cmd_name for cmd_name in _ALL_COMMAND_NAMES if cmd_name.startswith(text)
            ]
        if 0 <= state < len(_matches):
            return _matches[state]
        return None

    readline.set_completer(_completer)
    readline.parse_and_bind("tab: complete")


def _load_model_tokenizer(args):
    tokenizer = AutoTokenizer.from_pretrained(
        args.checkpoint_path,
        resume_download=True,
    )

    # Set bos_token for left-padding
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.bos_token

    device_map = "cpu" if args.cpu_only else "auto"

    model = AutoModelForCausalLM.from_pretrained(
        args.checkpoint_path,
        torch_dtype="auto",
        device_map=device_map,
        resume_download=True,
    ).eval()

    # Conservative generation config
    model.generation_config.max_new_tokens = 256
    model.generation_config.temperature = 0.7
    model.generation_config.top_k = 50
    model.generation_config.top_p = 0.9
    model.generation_config.pad_token_id = tokenizer.pad_token_id
    model.generation_config.eos_token_id = tokenizer.eos_token_id
    model.generation_config.do_sample = False

    return model, tokenizer


def _gc():
    import gc

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _clear_screen():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def _print_history(history):
    terminal_width = shutil.get_terminal_size()[0]
    print(f"History ({len(history)})".center(terminal_width, "="))
    for index, (query, response) in enumerate(history):
        print(f"User[{index}]: {query}")
        print(f"Qwen[{index}]: {response}")
    print("=" * terminal_width)


def _get_input() -> str:
    while True:
        try:
            message = input("User> ").strip()
        except UnicodeDecodeError:
            print("[ERROR] Encoding error in input")
            continue
        except KeyboardInterrupt:
            exit(1)
        if message:
            return message
        print("[ERROR] Query is empty")


def _chat_stream(model, tokenizer, query, history):
    conversation = []
    for query_h, response_h in history:
        conversation.append({"role": "user", "content": query_h})
        conversation.append({"role": "assistant", "content": response_h})
    conversation.append({"role": "user", "content": query})
    input_text = tokenizer.apply_chat_template(
        conversation,
        add_generation_prompt=True,
        tokenize=False,
    )
    # Perform left-padding with bos_token
    inputs = tokenizer(
        [input_text],
        return_tensors="pt",
        padding="longest",
        truncation=True,
        pad_to_multiple_of=8,
        max_length=1024,
        add_special_tokens=False
    ).to(model.device)

    # Update attention_mask for left-padding compatibility
    inputs["attention_mask"] = inputs["attention_mask"].flip(dims=[1])

    streamer = TextIteratorStreamer(
        tokenizer=tokenizer, skip_prompt=True, timeout=60.0, skip_special_tokens=True
    )
    generation_kwargs = {
        **inputs,
        "streamer": streamer,
    }
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    for new_text in streamer:
        yield new_text


def main():
    parser = argparse.ArgumentParser(
        description="Qwen2.5-Instruct command-line interactive chat demo."
    )
    parser.add_argument(
        "-c",
        "--checkpoint-path",
        type=str,
        default=DEFAULT_CKPT_PATH,
        help="Checkpoint name or path, default to %(default)r",
    )
    parser.add_argument("-s", "--seed", type=int, default=1234, help="Random seed")
    parser.add_argument(
        "--cpu-only", action="store_true", help="Run demo with CPU only"
    )
    args = parser.parse_args()

    history, response = [], ""

    model, tokenizer = _load_model_tokenizer(args)
    orig_gen_config = deepcopy(model.generation_config)

    _setup_readline()

    _clear_screen()
    print(_WELCOME_MSG)

    seed = args.seed

    while True:
        query = _get_input()

        # Process commands.
        if query.startswith(":"):
            command_words = query[1:].strip().split()
            if not command_words:
                command = ""
            else:
                command = command_words[0]

            if command in ["exit", "quit", "q"]:
                break
            elif command in ["clear", "cl"]:
                _clear_screen()
                print(_WELCOME_MSG)
                _gc()
                continue
            elif command in ["clear-history", "clh"]:
                print(f"[INFO] All {len(history)} history cleared")
                history.clear()
                _gc()
                continue
            elif command in ["help", "h"]:
                print(_HELP_MSG)
                continue
            elif command in ["history", "his"]:
                _print_history(history)
                continue
            elif command in ["seed"]:
                if len(command_words) == 1:
                    print(f"[INFO] Current random seed: {seed}")
                    continue
                else:
                    new_seed_s = command_words[1]
                    try:
                        new_seed = int(new_seed_s)
                    except ValueError:
                        print(
                            f"[WARNING] Fail to change random seed: {new_seed_s!r} is not a valid number"
                        )
                    else:
                        print(f"[INFO] Random seed changed to {new_seed}")
                        seed = new_seed
                    continue
            elif command in ["conf"]:
                if len(command_words) == 1:
                    print(model.generation_config)
                else:
                    for key_value_pairs_str in command_words[1:]:
                        eq_idx = key_value_pairs_str.find("=")
                        if eq_idx == -1:
                            print("[WARNING] format: <key>=<value>")
                            continue
                        conf_key, conf_value_str = (
                            key_value_pairs_str[:eq_idx],
                            key_value_pairs_str[eq_idx + 1 :],
                        )
                        try:
                            conf_value = eval(conf_value_str)
                        except Exception as e:
                            print(e)
                            continue
                        else:
                            print(
                                f"[INFO] Change config: model.generation_config.{conf_key} = {conf_value}"
                            )
                            setattr(model.generation_config, conf_key, conf_value)
                continue
            elif command in ["reset-conf"]:
                print("[INFO] Reset generation config")
                model.generation_config = deepcopy(orig_gen_config)
                print(model.generation_config)
                continue

        # Run chat.
        set_seed(seed)
        _clear_screen()
        print(f"\nUser: {query}")
        print(f"\nQwen: ", end="")
        try:
            partial_text = ""
            for new_text in _chat_stream(model, tokenizer, query, history):
                print(new_text, end="", flush=True)
                partial_text += new_text
            response = partial_text
            print()

        except KeyboardInterrupt:
            print("[WARNING] Generation interrupted")
            continue

        history.append((query, response))


if __name__ == "__main__":
    main()

