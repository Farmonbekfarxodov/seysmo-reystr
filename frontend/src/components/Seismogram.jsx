import React from "react";

// A hand-tuned seismic trace: flat baseline, two "event" bursts, tapering
// back to flat. This is the page's signature element (see design plan).
const WAVEFORM_PATH =
  "M0,40 L20,40 L35,38 L50,42 L65,20 L80,60 L95,10 L110,70 L125,25 L140,55 " +
  "L155,40 L170,40 L190,40 L205,36 L220,44 L235,15 L250,65 L265,40 L285,40 " +
  "L300,40 L320,40 L335,38 L350,42 L365,40 L385,40 L400,40 L420,40 L435,30 " +
  "L450,50 L465,40 L485,40 L500,40 L520,40 L535,42 L550,38 L565,40 L585,40 " +
  "L600,40 L620,40 L635,40 L650,40 L670,40 L685,40 L700,40 L720,40 L735,40 " +
  "L750,40 L770,40 L785,40 L800,40";

export default function Seismogram({ className = "", strokeWidth = 2 }) {
  return (
    <svg
      viewBox="0 0 800 80"
      preserveAspectRatio="none"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      <path
        d={WAVEFORM_PATH}
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        className="seismogram-path"
      />
    </svg>
  );
}
