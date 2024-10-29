import React from 'react';
import { Form, Field } from 'react-final-form';

interface FormValues {
    healthGoal: string;
    dietType?: string;
    exerciseLevel?: string;
    hydrationGoal?: string;
    userInput: string;
}

const EatingForm: React.FC = () => {
    const onSubmit = (values: FormValues) => {
        console.log('Form values:', values);
    };

    return (
        <Form<FormValues>
            onSubmit={onSubmit}
            render={({ handleSubmit, form }) => {
                const healthGoal = form.getFieldState("healthGoal")?.value;

                return (
                    <form onSubmit={handleSubmit} className="flex flex-col items-center p-8 bg-gray-100 rounded-lg shadow-lg max-w-md mx-auto">
                        <h2 className="text-2xl font-semibold text-gray-800 mb-6">Select Your Health Goal</h2>

                        {/* Health Goal Selection */}
                        <div className="w-full mb-4">
                            <label className="text-gray-700 mb-2 block">Health Goal</label>
                            <Field<string> name="healthGoal" component="select" className="w-full p-3 border border-gray-300 rounded-lg text-gray-800 focus:outline-none focus:border-blue-500">
                                <option value="">Select your goal</option>
                                <option value="weight_loss">Weight Loss</option>
                                <option value="muscle_gain">Muscle Gain</option>
                                <option value="improve_energy">Improve Energy</option>
                                <option value="enhance_focus">Enhance Focus</option>
                                <option value="general_health">General Health</option>
                            </Field>
                        </div>

                        {/* Dynamic Fields Based on Health Goal */}
                        {healthGoal === 'weight_loss' && (
                            <div className="w-full mb-4">
                                <label className="text-gray-700 mb-2 block">Diet Type</label>
                                <Field<string> name="dietType" component="select" className="w-full p-3 border border-gray-300 rounded-lg text-gray-800 focus:outline-none focus:border-blue-500">
                                    <option value="">Select diet type</option>
                                    <option value="keto">Keto</option>
                                    <option value="low_carb">Low Carb</option>
                                    <option value="intermittent_fasting">Intermittent Fasting</option>
                                    <option value="mediterranean">Mediterranean</option>
                                </Field>
                            </div>
                        )}

                        {healthGoal === 'muscle_gain' && (
                            <div className="w-full mb-4">
                                <label className="text-gray-700 mb-2 block">Exercise Level</label>
                                <Field<string> name="exerciseLevel" component="select" className="w-full p-3 border border-gray-300 rounded-lg text-gray-800 focus:outline-none focus:border-blue-500">
                                    <option value="">Select exercise level</option>
                                    <option value="beginner">Beginner</option>
                                    <option value="intermediate">Intermediate</option>
                                    <option value="advanced">Advanced</option>
                                </Field>
                            </div>
                        )}

                        {healthGoal === 'improve_energy' && (
                            <div className="w-full mb-4">
                                <label className="text-gray-700 mb-2 block">Hydration Goal</label>
                                <Field<string> name="hydrationGoal" component="select" className="w-full p-3 border border-gray-300 rounded-lg text-gray-800 focus:outline-none focus:border-blue-500">
                                    <option value="">Select hydration goal</option>
                                    <option value="2_liters">2 Liters</option>
                                    <option value="3_liters">3 Liters</option>
                                    <option value="4_liters">4 Liters</option>
                                </Field>
                            </div>
                        )}

                        {/* User Input */}
                        <div className="w-full mb-4">
                            <label className="text-gray-700 mb-2 block">Your Preferences</label>
                            <Field<string>
                                name="userInput"
                                component="input"
                                type="text"
                                placeholder="Enter your preferences or comments"
                                className="w-full p-3 border border-gray-300 rounded-lg text-gray-800 focus:outline-none focus:border-blue-500"
                            />
                        </div>

                        <button type="submit" className="px-6 py-3 text-white bg-blue-500 rounded-lg hover:bg-blue-600 transition-colors">
                            Submit
                        </button>
                    </form>
                );
            }}
        />
    );
};

export default EatingForm;
