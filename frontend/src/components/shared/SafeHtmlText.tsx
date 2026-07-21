import DOMPurify from "dompurify";

interface SafeHtmlTextProps {
  text: string;
  className?: string;
}

export function SafeHtmlText({ text, className = "" }: SafeHtmlTextProps) {
  if (!text) return null;

  // Check if text has any HTML tags (e.g., <p>, <ul>, <li>, <br>)
  const hasHtml = /<[a-z][\s\S]*>/i.test(text);

  if (hasHtml) {
    const sanitizedHtml = DOMPurify.sanitize(text);

    return (
      <div
        className={`safe-html-content ${className}`}
        dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
      />
    );
  }

  return (
    <p className={`whitespace-pre-line ${className}`}>
      {text}
    </p>
  );
}
