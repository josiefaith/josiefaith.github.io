import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Files starting with "_" (templates) are ignored by the loaders.

const releases = defineCollection({
  loader: glob({ pattern: '**/[^_]*.md', base: './src/content/releases' }),
  schema: z.object({
    title: z.string(),
    type: z.enum(['album', 'ep', 'single']),
    status: z.enum(['released', 'teaser']).default('released'),
    date: z.coerce.date().optional(),
    art: z.string().optional(), // filename under public/art/
    tagline: z.string().optional(),
    tracklist: z.array(z.string()).default([]),
    links: z
      .object({
        spotify: z.string().url().optional(),
        apple: z.string().url().optional(),
        youtube: z.string().url().optional(),
      })
      .default({}),
    featured: z.boolean().default(false),
  }),
});

const songs = defineCollection({
  loader: glob({ pattern: '**/[^_]*.md', base: './src/content/songs' }),
  schema: z.object({
    title: z.string(),
    release: z.string().optional(), // slug of the release it appears on
    listen: z.string().url().optional(),
    excerpt: z.string().optional(), // one line shown on the index
    lyrics: z.string().optional(), // full or partial lyrics, shown after the story
    order: z.number().default(0),
    draft: z.boolean().default(false), // drafts render in dev only
  }),
});

const shows = defineCollection({
  loader: glob({ pattern: '**/[^_]*.md', base: './src/content/shows' }),
  schema: z.object({
    date: z.coerce.date(),
    venue: z.string(),
    city: z.string(),
    time: z.string().optional(),
    link: z.string().url().optional(),
    note: z.string().optional(),
  }),
});

export const collections = { releases, songs, shows };
