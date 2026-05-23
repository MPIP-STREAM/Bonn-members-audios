# Bonn Members Audios

A simple GitHub Pages site where members of the Bonn group can hear how each other pronounces their own names.

## 🔊 Live Site

Visit the page at: **https://mpip-stream.github.io/Bonn-members-audios/**

## 📁 Repository Structure

```
├── audios/          # Audio files (one per person, e.g. anna.mp3)
├── names.md         # List of members and their audio file names
├── index.html       # GitHub Pages site with the audio player UI
└── README.md        # This file
```

## ➕ Adding a New Member

1. Record a short audio clip of yourself pronouncing your name (`.mp3` or `.wav`).
2. Name the file using your first and last name in lowercase, e.g. `anna_bonn.mp3`.
3. Place the file in the `audios/` folder.
4. Add a row for yourself in `names.md`.
5. Open a pull request — the site updates automatically once merged.

## 🛠 Local Development

Just open `index.html` in your browser. No build step required.
