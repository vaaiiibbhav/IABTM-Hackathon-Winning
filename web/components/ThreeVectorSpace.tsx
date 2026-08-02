"use client";

import React from "react";
import TwinVisualization from "./TwinVisualization";
import type { Theme } from "../lib/types";

interface ThreeVectorSpaceProps {
  themes: Theme[];
  driftScore: number;
}

export default function ThreeVectorSpace({ themes, driftScore }: ThreeVectorSpaceProps) {
  // Drive alignmentValue from driftScore: alignment = 1 - driftScore
  const alignmentValue = Math.max(0, Math.min(1, 1 - driftScore));
  return <TwinVisualization alignmentValue={alignmentValue} />;
}
