## **Introduction**

**Picre** is a Playblasts In-Context Reviewer designed for animators who use Maya. 
It is a small, artist-facing tool that makes reviewing shots in context faster, without the need to publish on Flow first. 
It has two components: a _Playblast Manager_ and a _Playblasts Reviewer_.

## **Playblast Manager**
- It captures the scene settings, reading the active camera, frame range and resolution;
- It validates names and paths, ensuring every playblast lands in the right folder with the right name at the next version;
- It adds burn-in overlays.

## **Playblasts Reviewer**
- It scans the folder where the playblasts have been exported and shows the animator what’s in there. 
- The artist ticks the shots they want to review in context, and the tool stitches them into a single clip (each shot will be recognisable thanks to the burn-ins added by the playblast manager).
