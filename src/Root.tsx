import React from "react";
import { Composition } from "remotion";
import { MoEVisualizerPreview } from "./compositions/MoEVisualizerPreview";
import "./style.css";

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="MoEVisualizerPreview"
        component={MoEVisualizerPreview}
        durationInFrames={210} // 7 seconds at 30fps; fits Kokoro narration
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
        durationInFrames={210}
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
