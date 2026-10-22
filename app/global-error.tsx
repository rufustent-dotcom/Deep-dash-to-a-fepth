'use client';

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="flex flex-col items-center justify-center min-h-screen bg-zinc-950 text-zinc-400 font-mono p-6 text-center">
        <h2 className="text-xl text-red-500 font-bold mb-2">Something went wrong</h2>
        <p className="text-xs text-zinc-500 max-w-md mb-6">
          A critical system error occurred.
        </p>
        <button
          onClick={() => reset()}
          className="px-4 py-2 bg-zinc-900 border border-zinc-800 text-xs text-zinc-200 rounded hover:border-zinc-700 cursor-pointer"
        >
          Try again
        </button>
      </body>
    </html>
  );
}
