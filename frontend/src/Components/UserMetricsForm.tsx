import React, { useState } from "react";
import { Form, Field, FieldRenderProps } from "react-final-form";
import Slider from "@mui/material/Slider";

interface FormValues {
  age?: number;
  height?: number;
  weight?: number;
}

const UserMetricsForm: React.FC = () => {
  const [stage, setStage] = useState<number>(1);

  const next = () => setStage((prev) => prev + 1);
  const previous = () => setStage((prev) => prev - 1);

  const onSubmit = (values: FormValues) => {
    console.log("Form submitted:", values);
  };

  // Helper function to select emoji based on value
  const selectEmoji = (value: number | undefined, thresholds: number[], emojis: (string | JSX.Element)[]) => {
    if (value === undefined) return null;
    if (value <= thresholds[0]) return emojis[0];
    if (value <= thresholds[1]) return emojis[1];
    return emojis[2];
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-200">
      <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-8 text-center">
        <h1 className="text-2xl font-bold text-gray-700 mb-6">
          User Metrics Form
        </h1>
        <Form<FormValues>
          onSubmit={onSubmit}
          render={({ handleSubmit, values }) => (
            <form onSubmit={handleSubmit}>
              {/* Stage 1: Age */}
              {stage === 1 && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-600 mb-4">
                    Stage 1: Age
                  </h2>
                  <div className="text-3xl mb-4">
                    {selectEmoji(values.age, [17, 50], ["👶", "🧑", "👴"])}
                  </div>
                  <div className="mb-4">
                    <label htmlFor="age" className="block text-gray-500 mb-2">
                      Age
                    </label>
                    <Field<number>
                      name="age"
                      parse={(value) => (value === undefined ? 0 : Number(value))} // Changed to return 0 instead of undefined
                    >
                      {({ input, meta }) => (
                        <div>
                          <input
                            {...input}
                            id="age"
                            type="number"
                            placeholder="Enter age"
                            min={0}
                            max={100}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-indigo-500"
                          />
                          {meta.touched && meta.error && (
                            <span className="text-red-500 text-sm">{meta.error}</span>
                          )}
                        </div>
                      )}
                    </Field>
                  </div>
                  <div className="flex justify-center">
                    <button
                      type="button"
                      onClick={next}
                      className="px-4 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}

              {/* Stage 2: Height */}
              {stage === 2 && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-600 mb-4">
                    Stage 2: Height
                  </h2>
                  <div className="text-3xl mb-4">
                    {selectEmoji(values.height, [150, 175], ["🌼", "🧍🏻", "🦒"])}
                  </div>
                  <div className="mb-4">
                    <label htmlFor="height" className="block text-gray-500 mb-2">
                      Height (cm)
                    </label>
                    <Field<number>
                      name="height"
                      parse={(value) => (value === undefined ? 0 : Number(value))} // Changed to return 0 instead of undefined
                    >
                      {({ input, meta }) => (
                        <div>
                          <input
                            {...input}
                            id="height"
                            type="number"
                            placeholder="Enter height"
                            min={0}
                            max={250}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-indigo-500"
                          />
                          {meta.touched && meta.error && (
                            <span className="text-red-500 text-sm">{meta.error}</span>
                          )}
                        </div>
                      )}
                    </Field>
                  </div>
                  <div className="flex justify-between">
                    <button
                      type="button"
                      onClick={previous}
                      className="px-4 py-2 bg-gray-400 text-white rounded-md hover:bg-gray-500"
                    >
                      Previous
                    </button>
                    <button
                      type="button"
                      onClick={next}
                      className="px-4 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}

              {/* Stage 3: Weight */}
              {stage === 3 && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-600 mb-4">
                    Stage 3: Weight
                  </h2>
                  <div className="text-3xl mb-4">
                    {selectEmoji(values.weight, [70, 99], ["🐭", "🐱", "🐘"])}
                  </div>
                  <div className="mb-6">
                    <label htmlFor="weight" className="block text-gray-500 mb-2">
                      Weight (kg)
                    </label>
                    <Field<number> name="weight">
                      {({ input, meta }: FieldRenderProps<number, HTMLElement>) => (
                        <div>
                          <Slider
                            value={input.value || 0}
                            onChange={(_, value) => {
                              const newValue = Array.isArray(value) ? value[0] : value;
                              input.onChange(newValue);
                            }}
                            min={0}
                            max={200}
                            className="text-indigo-500"
                          />
                          <div className="text-gray-600 mt-2">
                            Weight: {input.value || 0} kg
                          </div>
                          {meta.touched && meta.error && (
                            <span className="text-red-500 text-sm">{meta.error}</span>
                          )}
                        </div>
                      )}
                    </Field>
                  </div>
                  <div className="flex justify-between">
                    <button
                      type="button"
                      onClick={previous}
                      className="px-4 py-2 bg-gray-400 text-white rounded-md hover:bg-gray-500"
                    >
                      Previous
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600"
                    >
                      Submit
                    </button>
                  </div>
                </div>
              )}
            </form>
          )}
        />
      </div>
    </div>
  );
};

export default UserMetricsForm;
