export function InlineError({ message }: { message: string }) {
  if (!message) return null;
  return (
    <div
      className="mb-6 p-4 rounded-lg bg-negative/10 text-negative text-sm"
      role="alert"
    >
      {message}
    </div>
  );
}
