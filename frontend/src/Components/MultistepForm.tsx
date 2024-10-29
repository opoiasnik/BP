import React, { useState } from "react";
import { Form, Field } from "react-final-form";
import Slider from "@mui/material/Slider";
import { useLazySendTestVersionQuery } from "../store/api/chatApi";
import { LuLoader2 } from "react-icons/lu";
import { Link } from "react-router-dom";
interface FormValues {
  age?: number;
  height?: number;
  weight?: number;
  healthGoal?: string;
  dietType?: string;
  exerciseLevel?: string;
  hydrationGoal?: string;
  userInput?: string;
}


const MultiStepForm: React.FC = () => {
  const [formValues, setFormValues] = useState<FormValues>({});
  const [stage, setStage] = useState<number>(1);
  const [data, setData] = useState<string | null>(null)

  const [sendTestMessage, { isLoading, isFetching }] = useLazySendTestVersionQuery()

  const nextStage = () => setStage((prev) => prev + 1);
  const previousStage = () => setStage((prev) => prev - 1);

  const saveFormData = (values: FormValues) => {
    setFormValues((prev) => ({
      ...prev,
      ...values,
    }));
  };

  const onSubmit = (values: FormValues) => {
    saveFormData(values);
    nextStage();
  };
  console.log(isLoading)

  const finalSubmit = async () => {
    const res = await sendTestMessage(formValues).unwrap()
    setData(res)
  };

  const selectEmoji = (
    value: number | undefined,
    thresholds: number[],
    emojis: string[]
  ) => {
    if (value === undefined) return null;
    if (value <= thresholds[0]) return emojis[0];
    if (value <= thresholds[1]) return emojis[1];
    return emojis[2];
  };

  return !data ? (
    <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-8 text-center">

      <h1 className="text-2xl font-bold text-gray-700 mb-6">
        Fill in your profile and get some advices
      </h1>

      <Form<FormValues>
        onSubmit={onSubmit}
        initialValues={formValues}
        render={({ handleSubmit, values }) => (
          <form onSubmit={handleSubmit}>
            {stage === 1 && (<> <div>
              <h2 className="text-xl font-semibold text-gray-600 mb-4">
                Stage 1: Base information
              </h2>
              <div className="text-3xl mb-4">
                {selectEmoji(values.age, [17, 50], ["👶", "🧑", "👴"])}
              </div>
              <Field
                name="age"
                parse={(value) => (value === "" ? 0 : Number(value))}
              >
                {({ input }) => (
                  <input
                    {...input}
                    type="number"
                    placeholder="Enter age"
                    min={0}
                    max={100}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-indigo-500"
                  />
                )}
              </Field>

            </div>



              <div>

                <div className="text-3xl mb-4">
                  {selectEmoji(values.height, [150, 175], ["🌱", "🌳", "🌲"])}
                </div>
                <Field
                  name="height"
                  parse={(value) => (value === "" ? 0 : Number(value))}
                >
                  {({ input }) => (
                    <input
                      {...input}
                      type="number"
                      placeholder="Enter height"
                      min={0}
                      max={250}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-indigo-500"
                    />
                  )}
                </Field>

              </div>
              <div >
                <h2 className="text-xl font-semibold text-gray-600 mb-4">
                </h2>
                <Field<string> name="dietType" component="select" className="w-full p-3 border border-gray-300 rounded-lg text-gray-800 focus:outline-none focus:border-blue-500">
                  <option value="">Select your goal</option>
                  <option value="weight_loss">Weight Loss</option>
                  <option value="muscle_gain">Muscle Gain</option>
                  <option value="improve_energy">Improve Energy</option>
                  <option value="enhance_focus">Enhance Focus</option>
                  <option value="general_health">General Health</option>
                </Field>

              </div>


              <div>
                <div className="text-3xl mb-4">
                  {selectEmoji(values.weight, [70, 99], ["🐭", "🐱", "🐘"])}
                </div>
                <Field
                  name="weight"
                  parse={(value) => (value === "" ? 0 : Number(value))}
                >
                  {({ input }) => (
                    <div>
                      <Slider
                        value={input.value || 0}
                        onChange={(_, value) =>
                          input.onChange(
                            Array.isArray(value) ? value[0] : value
                          )
                        }
                        min={0}
                        max={200}
                        className="text-indigo-500"
                      />
                      <div className="text-gray-600 mt-2">
                        Current Weight: {input.value || 0} kg
                      </div>
                    </div>
                  )}
                </Field>
                <div className="flex justify-end">

                  <button
                    type="button"
                    onClick={nextStage}
                    className="px-4 py-2 bg-bright-blue text-white rounded-md hover:bg-indigo-500"
                  >
                    Next
                  </button>
                </div>
              </div>
            </>)}


            {stage === 2 && (
              <>
                <div>
                  <h2 className="text-xl font-semibold text-gray-600 mb-4">
                    Stage 2: Details
                  </h2>


                </div>


                <div className="text-start">
                  <div className="mb-4">
                    <label className="text-gray-700 mb-2 block">Diet Type</label>
                    <Field<string> name="dietType" component="select" className="w-full p-3 border border-gray-300 rounded-lg text-gray-800 focus:outline-none focus:border-blue-500">
                      <option value="">Select diet type</option>
                      <option value="keto">Keto</option>
                      <option value="low_carb">Low Carb</option>
                      <option value="intermittent_fasting">Intermittent Fasting</option>
                      <option value="mediterranean">Mediterranean</option>
                    </Field>
                  </div>
                  <div className="mb-4">
                    <label className="text-gray-700 mb-2 block">Exercise Level</label>
                    <Field<string> name="exerciseLevel" component="select" className="w-full p-3 border border-gray-300 rounded-lg text-gray-800 focus:outline-none focus:border-blue-500">
                      <option value="">Select exercise level</option>
                      <option value="beginner">Beginner</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                    </Field>
                  </div>
                  <div className="mb-4">
                    <label className="text-gray-700 mb-2 block">Hydration Goal</label>
                    <Field<string> name="hydrationGoal" component="select" className="w-full p-3 border border-gray-300 rounded-lg text-gray-800 focus:outline-none focus:border-blue-500">
                      <option value="">Select hydration goal</option>
                      <option value="2_liters">2 Liters</option>
                      <option value="3_liters">3 Liters</option>
                      <option value="4_liters">4 Liters</option>
                    </Field>
                  </div>
                  <div className="mb-4">
                    <label className="text-gray-700 mb-2 block">Your Preferences</label>
                    <Field<string> name="userInput" component="input" type="text" placeholder="Enter your preferences or comments" className="w-full p-3 border border-gray-300 rounded-lg text-gray-800 focus:outline-none focus:border-blue-500" />
                  </div>
                  <div className="flex justify-between">
                    <button type="button" onClick={previousStage} className="px-4 py-2 bg-gray-400 text-white rounded-md hover:bg-gray-500">
                      Previous
                    </button>
                    <button type="submit" className="px-4 py-2 bg-bright-blue text-white rounded-md hover:bg-indigo-500">
                      Next
                    </button>
                  </div>
                </div>
              </>
            )}
            {stage === 3 && (
              <div className="text-start">
                <h2 className="text-xl font-semibold text-gray-600 mb-4 text-center">Summary</h2>
                <p><strong>Age:</strong> {formValues.age}</p>
                <p><strong>Height:</strong> {formValues.height} cm</p>
                <p><strong>Weight:</strong> {formValues.weight} kg</p>
                <p><strong>Health Goal:</strong> {formValues.healthGoal}</p>
                <p><strong>Diet Type:</strong> {formValues.dietType || "Not specified"}</p>
                <p><strong>Exercise Level:</strong> {formValues.exerciseLevel || "Not specified"}</p>
                <p><strong>Hydration Goal:</strong> {formValues.hydrationGoal || "Not specified"}</p>
                <p><strong>User Input:</strong> {formValues.userInput || "Not specified"}</p>
                <div className="flex justify-between mt-4">
                  <button type="button" disabled={isLoading} onClick={previousStage} className="px-4 py-2 bg-gray-400 text-white rounded-md hover:bg-gray-500">
                    Previous
                  </button>
                  <button type="button" disabled={isLoading} onClick={finalSubmit} className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600">
                    {isLoading || isFetching ? <LuLoader2 className="animate-spin" /> : 'Confirm'}
                  </button>
                </div>
              </div>
            )}
          </form>
        )}
      />
    </div>
  ) : (<div className="w-full flex flex-col items-center gap-6">
    <h1 className="text-4xl flex items-center sm:text-5xl md:text-6xl font-semibold mb-4 text-center text-dark-blue">
      Advices for your health
    </h1>
    <p className="w-1/2">{data}</p>
    <div className="flex gap-2 items-center">
      <Link to='/dashboard'>
        <button className="bg-bright-blue text-white font-medium py-2 px-5 rounded hover:bg-deep-blue transition duration-300 shadow-md">
          Get started with full version
        </button>
      </Link>
      <button onClick={() => { setData(null), setStage(1) }} className="px-4 py-2 bg-gray-400 text-white rounded-md hover:bg-gray-500">
        Try again
      </button>

    </div>
  </div>
  )
};

export default MultiStepForm;
