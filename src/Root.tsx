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
