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
        calculateMetadata={({ props }: { props: any }) => {
          const vsg = props?.vsg || (props?.metadata ? props : undefined);
          const totalFrames = vsg?.metadata?.canvas?.total_frames || 600;
          return {
            durationInFrames: totalFrames,
            fps: vsg?.metadata?.canvas?.fps || 60,
            width: vsg?.metadata?.canvas?.width_px || 1080,
            height: vsg?.metadata?.canvas?.height_px || 1920,
          };
        }}
        durationInFrames={600}
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
        calculateMetadata={({ props }: { props: any }) => {
          const vsg = props?.vsg || (props?.metadata ? props : undefined);
          const totalFrames = vsg?.metadata?.canvas?.total_frames || 600;
          return {
            durationInFrames: totalFrames,
            fps: vsg?.metadata?.canvas?.fps || 60,
            width: vsg?.metadata?.canvas?.width_px || 1080,
            height: vsg?.metadata?.canvas?.height_px || 1920,
          };
        }}
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

