// A safe, native way to decode all HTML entities (&#8212;, &#163;, &amp;, etc.)
export const decodeHTML = (html) => {
  if (!html) return '';

  let fixedText = html.replace(/(?:&#163;|163;)/g, '£');
  const txt = document.createElement("textarea");
  txt.innerHTML = fixedText;
  
  return txt.value;
};