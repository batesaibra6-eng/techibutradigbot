'use client';

import { useState } from 'react';

export default function Apply() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    fullName: '',
    gender: '',
    dob: '',
    nationality: 'Ugandan',
    previousSchool: '',
    applyingFor: 'O-Level',
    parentName: '',
    parentPhone: '',
    parentEmail: '',
    address: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const nextStep = () => setStep(step + 1);
  const prevStep = () => setStep(step - 1);

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <div className="flex items-center justify-between mb-12">
          <div>
            <a href="/" className="text-sm text-[#0a5c36] hover:underline">← Back to Home</a>
            <h1 className="text-5xl font-semibold tracking-tighter mt-3">Online Application</h1>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500">STEP {step} OF 4</div>
            <div className="font-mono text-sm tracking-widest text-[#0a5c36]">2026 INTAKE</div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="h-px bg-gray-200 mb-12">
          <div className="h-px bg-[#0a5c36] transition-all" style={{ width: `${(step / 4) * 100}%` }} />
        </div>

        {step === 1 && (
          <div>
            <h2 className="font-semibold text-3xl mb-8 tracking-tight">Student Information</h2>
            <div className="space-y-6">
              <div>
                <label className="text-sm font-medium text-gray-600">Full Legal Name</label>
                <input type="text" name="fullName" value={formData.fullName} onChange={handleChange} className="mt-1.5 block w-full border border-gray-300 px-4 py-3.5 rounded-xl" placeholder="John Doe" />
              </div>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="text-sm font-medium text-gray-600">Gender</label>
                  <select name="gender" value={formData.gender} onChange={handleChange} className="mt-1.5 block w-full border border-gray-300 px-4 py-3.5 rounded-xl">
                    <option value="">Select</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Date of Birth</label>
                  <input type="date" name="dob" value={formData.dob} onChange={handleChange} className="mt-1.5 block w-full border border-gray-300 px-4 py-3.5 rounded-xl" />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Previous School</label>
                <input type="text" name="previousSchool" value={formData.previousSchool} onChange={handleChange} className="mt-1.5 block w-full border border-gray-300 px-4 py-3.5 rounded-xl" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Applying For</label>
                <select name="applyingFor" value={formData.applyingFor} onChange={handleChange} className="mt-1.5 block w-full border border-gray-300 px-4 py-3.5 rounded-xl">
                  <option value="O-Level">O-Level (S1–S4)</option>
                  <option value="A-Level">A-Level (S5–S6)</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {step === 2 && (
          <div>
            <h2 className="font-semibold text-3xl mb-8 tracking-tight">Parent / Guardian Details</h2>
            <div className="space-y-6">
              <div>
                <label className="text-sm font-medium text-gray-600">Parent/Guardian Full Name</label>
                <input type="text" name="parentName" value={formData.parentName} onChange={handleChange} className="mt-1.5 block w-full border border-gray-300 px-4 py-3.5 rounded-xl" />
              </div>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="text-sm font-medium text-gray-600">Phone Number</label>
                  <input type="tel" name="parentPhone" value={formData.parentPhone} onChange={handleChange} className="mt-1.5 block w-full border border-gray-300 px-4 py-3.5 rounded-xl" placeholder="+256 7XX XXX XXX" />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Email Address</label>
                  <input type="email" name="parentEmail" value={formData.parentEmail} onChange={handleChange} className="mt-1.5 block w-full border border-gray-300 px-4 py-3.5 rounded-xl" />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Home Address</label>
                <textarea name="address" value={formData.address} onChange={handleChange} rows={3} className="mt-1.5 block w-full border border-gray-300 px-4 py-3.5 rounded-xl resize-y" />
              </div>
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <h2 className="font-semibold text-3xl mb-8 tracking-tight">Document Upload</h2>
            <div className="space-y-6">
              <div className="border border-dashed border-gray-300 rounded-2xl p-9 text-center">
                <div className="mx-auto w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center mb-4">📄</div>
                <div className="font-medium">Upload Academic Documents</div>
                <div className="text-sm text-gray-500 mt-1">PLE results, report cards, or transcripts (PDF, max 5MB)</div>
                <button className="mt-4 px-6 py-2 text-sm rounded-full border">Choose Files</button>
              </div>

              <div className="border border-dashed border-gray-300 rounded-2xl p-9 text-center">
                <div className="mx-auto w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center mb-4">🖼️</div>
                <div className="font-medium">Passport Size Photograph</div>
                <div className="text-sm text-gray-500 mt-1">Recent color photo on white background (JPG/PNG)</div>
                <button className="mt-4 px-6 py-2 text-sm rounded-full border">Upload Photo</button>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-6">You can upload documents later from your applicant dashboard.</p>
          </div>
        )}

        {step === 4 && (
          <div className="text-center py-8">
            <div className="text-6xl mb-6">🎉</div>
            <h2 className="text-4xl font-semibold tracking-tight mb-3">Application Submitted!</h2>
            <p className="text-lg text-gray-600 max-w-xs mx-auto">Thank you. Your application reference number is <span className="font-mono font-medium text-[#0a5c36]">ML-2026-18492</span>.</p>
            
            <div className="mt-10">
              <a href="/" className="inline-block px-8 py-3.5 rounded-full bg-[#0a5c36] text-white font-medium">Return to Homepage</a>
            </div>
            <div className="mt-4 text-xs text-gray-500">You will receive an email with login credentials to track your application.</div>
          </div>
        )}

        {/* Navigation */}
        {step < 4 && (
          <div className="flex items-center justify-between mt-14">
            <button 
              onClick={prevStep} 
              disabled={step === 1}
              className="text-sm disabled:opacity-30 px-5 py-3 rounded-full border"
            >
              ← Back
            </button>
            <button 
              onClick={nextStep} 
              className="px-9 py-3.5 rounded-full bg-[#0a5c36] text-white font-medium"
            >
              {step === 3 ? 'Submit Application' : 'Continue →'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
