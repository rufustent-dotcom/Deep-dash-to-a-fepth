import type { Metadata } from 'next';
import React from 'react';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Strategic Intelligence Vault',
  description:
    'An interactive strategic intelligence workspace and pattern mapping index powered by Gemini, synthesizing signals, patterns, active projects, and Obsidian-style database folders.',
  openGraph: {
    title: 'AI Strategic Intelligence Vault',
    description:
      'An interactive strategic intelligence workspace and pattern mapping index powered by Gemini, synthesizing signals, patterns, active projects, and Obsidian-style database folders.',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}

