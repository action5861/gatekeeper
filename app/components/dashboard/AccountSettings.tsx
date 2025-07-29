'use client'

import { DollarSign, Globe, Save, Settings } from 'lucide-react'
import { useState } from 'react'

interface AccountSettingsProps {
    initialSettings?: {
        websiteUrl: string
        dailyBudget: number
        companyName: string
    }
}

export default function AccountSettings({ initialSettings }: AccountSettingsProps) {
    const [settings, setSettings] = useState({
        websiteUrl: initialSettings?.websiteUrl || '',
        dailyBudget: initialSettings?.dailyBudget || 10000,
        companyName: initialSettings?.companyName || '',
    })
    const [isEditing, setIsEditing] = useState(false)
    const [isSaving, setIsSaving] = useState(false)

    const handleSave = async () => {
        setIsSaving(true)
        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000))
            setIsEditing(false)
            // Here you would typically make an API call to save the settings
        } catch (error) {
            console.error('Failed to save settings:', error)
        } finally {
            setIsSaving(false)
        }
    }

    const handleCancel = () => {
        setSettings({
            websiteUrl: initialSettings?.websiteUrl || '',
            dailyBudget: initialSettings?.dailyBudget || 10000,
            companyName: initialSettings?.companyName || '',
        })
        setIsEditing(false)
    }

    return (
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-6 animate-fadeInUp">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-slate-100">Account Settings</h2>
                <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg flex items-center justify-center">
                    <Settings className="w-5 h-5 text-white" />
                </div>
            </div>

            <div className="space-y-6">
                {/* Company Name */}
                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        Company Name
                    </label>
                    {isEditing ? (
                        <input
                            type="text"
                            value={settings.companyName}
                            onChange={(e) => setSettings({ ...settings, companyName: e.target.value })}
                            className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                            placeholder="Enter your company name"
                        />
                    ) : (
                        <div className="px-4 py-3 bg-slate-700/30 rounded-lg border border-slate-600">
                            <p className="text-slate-100">{settings.companyName || 'Not set'}</p>
                        </div>
                    )}
                </div>

                {/* Website URL */}
                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        <Globe className="w-4 h-4 inline mr-2" />
                        Website URL
                    </label>
                    {isEditing ? (
                        <input
                            type="url"
                            value={settings.websiteUrl}
                            onChange={(e) => setSettings({ ...settings, websiteUrl: e.target.value })}
                            className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                            placeholder="https://your-website.com"
                        />
                    ) : (
                        <div className="px-4 py-3 bg-slate-700/30 rounded-lg border border-slate-600">
                            <p className="text-slate-100">
                                {settings.websiteUrl ? (
                                    <a
                                        href={settings.websiteUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-400 hover:text-blue-300 transition-colors duration-200"
                                    >
                                        {settings.websiteUrl}
                                    </a>
                                ) : (
                                    'Not set'
                                )}
                            </p>
                        </div>
                    )}
                </div>

                {/* Daily Budget */}
                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        <DollarSign className="w-4 h-4 inline mr-2" />
                        Daily Budget (₩)
                    </label>
                    {isEditing ? (
                        <input
                            type="number"
                            value={settings.dailyBudget}
                            onChange={(e) => setSettings({ ...settings, dailyBudget: parseInt(e.target.value) || 0 })}
                            className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                            placeholder="10000"
                            min="0"
                        />
                    ) : (
                        <div className="px-4 py-3 bg-slate-700/30 rounded-lg border border-slate-600">
                            <p className="text-slate-100">₩{settings.dailyBudget.toLocaleString()}</p>
                        </div>
                    )}
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-3 pt-4">
                    {isEditing ? (
                        <>
                            <button
                                onClick={handleSave}
                                disabled={isSaving}
                                className="flex-1 bg-gradient-to-r from-blue-500 to-green-500 hover:from-blue-600 hover:to-green-600 text-white font-semibold py-2 px-4 rounded-lg transition-all duration-200 transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                            >
                                {isSaving ? (
                                    <div className="flex items-center justify-center space-x-2">
                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                        <span>Saving...</span>
                                    </div>
                                ) : (
                                    <div className="flex items-center justify-center space-x-2">
                                        <Save className="w-4 h-4" />
                                        <span>Save Changes</span>
                                    </div>
                                )}
                            </button>
                            <button
                                onClick={handleCancel}
                                className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-slate-200 font-medium rounded-lg transition-all duration-200"
                            >
                                Cancel
                            </button>
                        </>
                    ) : (
                        <button
                            onClick={() => setIsEditing(true)}
                            className="flex-1 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-semibold py-2 px-4 rounded-lg transition-all duration-200 transform hover:scale-105 active:scale-95"
                        >
                            <div className="flex items-center justify-center space-x-2">
                                <Settings className="w-4 h-4" />
                                <span>Edit Settings</span>
                            </div>
                        </button>
                    )}
                </div>
            </div>
        </div>
    )
} 