# Premium 3D Domino UI Implementation Plan

## Goal
Redesign the domino UI to a state-of-the-art, seasoned pro-level standard featuring a premium, futuristic aesthetic.

## The New Aesthetic: 3D Glassmorphism & Neon
Instead of physical wooden dominos, we will build **Sleek Data Tiles** that cascade in 3D space.

### 1. Coloring & Materials (Glassmorphism)
- **Base Tiles**: Translucent dark glass (`rgba(255,255,255, 0.03)`) with a strong background blur, subtle glowing borders, and an inner frosted lighting effect.
- **Indicators (Dots)**: Minimalist glowing LED indicators using the existing cyan/purple gradients.
- **Active State**: The currently running tile will levitate smoothly, casting a rich, pulsing cyan/purple volumetric glow to indicate AI processing.

### 2. The Animation (True 3D Physics)
- Introduce `perspective: 1200px` and `transform-style: preserve-3d` to the container.
- When a tile completes, it smoothly tips over in a 3D arc, cascading onto the next tile. 
- The lighting and shadows will dynamically shift as the tile falls to give a true sense of depth.

## Implementation Steps
1. Re-write the `.domino-*` classes in `styles.css`.
2. Apply `perspective` and advanced `transform` operations.
