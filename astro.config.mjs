// @ts-check
import { defineConfig } from 'astro/config';

// `site` is used for canonical URLs once deployed to GitHub Pages.
// User-site repo (josiefaith.github.io) serves at the root — no `base` needed.
export default defineConfig({
  site: 'https://josiefaith.github.io',
});
