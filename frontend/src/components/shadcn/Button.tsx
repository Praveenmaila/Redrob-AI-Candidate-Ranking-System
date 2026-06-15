"use client";
import React from "react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "ghost" | "primary";
};

export default function Button({
  variant = "default",
  className = "",
  children,
  ...rest
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center px-3 py-1 rounded-md text-sm";
  const vstyles: Record<string, string> = {
    default: "bg-gray-100 text-gray-800 hover:bg-gray-200",
    ghost: "bg-transparent text-indigo-600 hover:bg-gray-50",
    primary: "bg-indigo-600 text-white hover:bg-indigo-700",
  };
  return (
    <button className={`${base} ${vstyles[variant]} ${className}`} {...rest}>
      {children}
    </button>
  );
}
