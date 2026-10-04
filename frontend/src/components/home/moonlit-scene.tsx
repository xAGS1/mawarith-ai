/** Original vector artwork: arches, moonlight and a quiet architectural skyline. */
export function MoonlitScene({ miniature = false }: { miniature?: boolean }) {
  const id = miniature ? "path" : "hero";
  return (
    <svg
      className={miniature ? "path-scene" : "moonlit-scene"}
      viewBox="0 0 680 470"
      fill="none"
      aria-hidden="true"
    >
      <defs>
        <linearGradient
          id={`${id}-sky`}
          x2="0"
          y2="470"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#063b43" />
          <stop offset="1" stopColor="#13676a" />
        </linearGradient>
        <linearGradient id={`${id}-stone`} x1="0%" y1="0%" x2="100%" y2="60%">
          <stop stopColor="#e5c48b" />
          <stop offset=".5" stopColor="#967145" />
          <stop offset="1" stopColor="#e0be83" />
        </linearGradient>
        <radialGradient id={`${id}-glow`}>
          <stop stopColor="#f4dfad" stopOpacity=".55" />
          <stop offset="1" stopColor="#f4dfad" stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`${id}-dome`} x2="0%" y2="100%">
          <stop stopColor="#439496" />
          <stop offset="1" stopColor="#0d5158" />
        </linearGradient>
        <filter
          id={`${id}-bloom`}
          x="-100%"
          y="-100%"
          width="300%"
          height="300%"
        >
          <feGaussianBlur stdDeviation="9" />
        </filter>
        <clipPath id={`${id}-opening`}>
          <path d="M100 465V185C100 70 269 52 340 0c71 52 240 70 240 185v280Z" />
        </clipPath>
        <pattern
          id={`${id}-lattice`}
          width="32"
          height="32"
          patternUnits="userSpaceOnUse"
        >
          <path
            d="m16 0 16 16-16 16L0 16Z M0 0l32 32M32 0 0 32"
            stroke="#d3b078"
            strokeWidth=".65"
            opacity=".38"
          />
        </pattern>
      </defs>
      <path
        d="M100 465V185C100 70 269 52 340 0c71 52 240 70 240 185v280Z"
        fill={`url(#${id}-sky)`}
      />
      <circle
        cx="425"
        cy="124"
        r="165"
        fill={`url(#${id}-glow)`}
        opacity=".65"
      />
      <path
        d="M445 75a44 44 0 1 0 22 66c-38 12-68-28-22-66Z"
        fill="#ffe9b5"
        filter={`url(#${id}-bloom)`}
        opacity=".5"
      />
      <path d="M445 75a44 44 0 1 0 22 66c-38 12-68-28-22-66Z" fill="#f4dfb1" />
      <path
        d="M439 81a39 39 0 0 0 27 57"
        stroke="#fff2d1"
        strokeWidth="2"
        opacity=".65"
      />
      {[
        [210, 115],
        [365, 67],
        [501, 170],
        [288, 153],
        [474, 55],
        [160, 207],
        [360, 178],
        [529, 240],
        [250, 85],
      ].map(([x, y]) => (
        <circle
          key={`${x}-${y}`}
          cx={x}
          cy={y}
          r="1.4"
          fill="#eed7ab"
          opacity=".6"
        />
      ))}
      <path
        d="m80 338 65-55 65 38 74-60 54 60 66-52 52 62 82-36 58 38v132H80Z"
        fill="#164c56"
      />
      <path
        d="m80 368 95-36 86 25 76-41 87 42 112-45 76 59v93H80Z"
        fill="#195e65"
      />
      <g clipPath={`url(#${id}-opening)`} opacity=".2" fill="#91b8a8">
        <path d="M110 400V345h14v-18h12v18h19v55m18 0v-43h20v-26h12v26h17v43m202 0v-48h18v-19h15v19h23v48m13 0v-63h17v-17h14v17h20v63" />
        <ellipse
          cx="350"
          cy="392"
          rx="260"
          ry="30"
          filter={`url(#${id}-bloom)`}
        />
      </g>
      <g fill="#0a424b">
        <path d="M214 466V314h228v152Z" />
        <path
          d="M259 314c0-36 43-60 70-94 27 34 70 58 70 94Z"
          fill={`url(#${id}-dome)`}
        />
        <path d="M329 225v-20" stroke="#dcc08a" />
        <path d="M333 199a5 5 0 1 1-6-7 5 5 0 0 0 6 7Z" fill="#dcc08a" />
        <path d="M186 464V278h26v186M445 464V251h26v213" />
        <path d="m182 280 17-17 17 17M441 252l17-18 17 18" fill="#d1ac71" />
        <path d="M190 263v-44l9-14 9 14v44M449 234v-51l9-14 9 14v51" />
        <path d="M181 290h37M440 264h37" stroke="#bda26c" strokeWidth="3" />
      </g>
      <g fill="#e9c886" opacity=".8">
        <path d="M317 397v-41q12-24 24 0v41Z" />
        <path d="M274 380v-20q7-14 14 0v20ZM371 380v-20q7-14 14 0v20Z" />
        <rect x="195" y="227" width="8" height="17" rx="4" />
        <rect x="454" y="193" width="8" height="17" rx="4" />
      </g>
      <path
        d="M102 469V185c0-115 168-133 238-185 70 52 238 70 238 185v284"
        stroke={`url(#${id}-stone)`}
        strokeWidth="36"
      />
      <path
        d="M120 468V187c0-98 150-119 220-167 70 48 220 69 220 167v281"
        stroke="#eed2a0"
        strokeOpacity=".4"
        strokeWidth="1.5"
      />
      <path
        d="M80 469V185c0-128 182-150 260-207 78 57 260 79 260 207v284"
        stroke="#d6b67d"
        strokeOpacity=".22"
        strokeWidth="2"
      />
      <path
        d="M93 465V185c0-119 172-139 247-192 75 53 247 73 247 192v280"
        stroke="#fff0cc"
        strokeOpacity=".22"
        strokeWidth="1"
      />
      <path
        d="M43 469V105h43v364M596 469V105h43v364"
        fill={`url(#${id}-lattice)`}
      />
      <path
        d="M40 105h48M592 105h50M30 460h65M585 460h67"
        stroke="#b5925c"
        strokeWidth="4"
      />
      <path d="M70 436h540v34H70Z" fill="#c6a577" opacity=".12" />
      <g transform="translate(503 357)">
        <path d="M0 0h20l7 12v40H-7V12Z" fill="#a9844f" />
        <path d="M0 14h20v31H0Z" fill="#e6bd73" />
        <path d="M10 0v-28" stroke="#c9a774" />
        <circle cx="10" cy="29" r="46" fill={`url(#${id}-glow)`} />
      </g>
    </svg>
  );
}
