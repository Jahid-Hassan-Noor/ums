export function ThemeScript() {
  const script = `
!function(){try{var t=localStorage.getItem("theme");var m=t==="dark"||(!t&&matchMedia("(prefers-color-scheme: dark)").matches);document.documentElement.classList.toggle("dark",m)}catch(e){}}();
`

  return <script dangerouslySetInnerHTML={{ __html: script }} />
}
