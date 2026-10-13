import React from "react";
import { Composition } from "remotion";
import { MoEVisualizerPreview } from "./compositions/MoEVisualizerPreview";
import { BroadcastComposition } from "./compositions/BroadcastComposition";
import "./style.css";

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="BroadcastComposition"
        component={BroadcastComposition}
        durationInFrames={600} // 10 seconds at 60fps default (overridable)
        fps={60}
        width={1080}
        height={1920}
        defaultProps={{
          showSafeZoneOverlay: false,
        }}
      />
      <Composition
        id="BroadcastCompositionWithSafeZone"
        component={BroadcastComposition}
        durationInFrames={600}
        fps={60}
        width={1080}
        height={1920}
        defaultProps={{
          showSafeZoneOverlay: true,
        }}
      />
      <Composition
        id="MoEVisualizerPreview"
        component={MoEVisualizerPreview}
        durationInFrames={180} // 6 seconds at 30fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          showSafeZoneOverlay: false,
        }}
      />
      <Composition
        id="MoEVisualizerWithSafeZone"
        component={MoEVisualizerPreview}
        durationInFrames={180}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          showSafeZoneOverlay: true,
        }}
      />
    </>
  );
};

