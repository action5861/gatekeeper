import React from 'react'

interface AlertProps {
    children: React.ReactNode
    variant?: 'default' | 'destructive' | 'success'
    className?: string
}

export function Alert({ children, variant = 'default', className = '' }: AlertProps) {
    const baseStyles = 'relative w-full rounded-lg border p-4'
    const variantStyles = {
        default: 'bg-blue-50 border-blue-200 text-blue-900',
        destructive: 'bg-red-50 border-red-200 text-red-900',
        success: 'bg-green-50 border-green-200 text-green-900',
    }

    return (
        <div className={`${baseStyles} ${variantStyles[variant]} ${className}`} role="alert">
            {children}
        </div>
    )
}

interface AlertTitleProps {
    children: React.ReactNode
    className?: string
}

export function AlertTitle({ children, className = '' }: AlertTitleProps) {
    return (
        <h5 className={`mb-1 font-medium leading-none tracking-tight ${className}`}>
            {children}
        </h5>
    )
}

interface AlertDescriptionProps {
    children: React.ReactNode
    className?: string
}

export function AlertDescription({ children, className = '' }: AlertDescriptionProps) {
    return <div className={`text-sm opacity-90 ${className}`}>{children}</div>
}

