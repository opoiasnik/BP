import React, { useState } from 'react';

export type Muscle = 'neck' | 'chest' | 'biceps' | 'forearms' | 'quadriceps' | 'calves' | 'abs' | 'shoulders' | 'trapezius';

const MuscleDiagram: React.FC = () => {
  const [highlightedMuscle, setHighlightedMuscle] = useState<Muscle | null>(null);

  const handleMouseEnter = (muscle: Muscle) => {
    setHighlightedMuscle(muscle);
  };

  const handleMouseLeave = () => {
    setHighlightedMuscle(null);
  };

  const handleMuscleClick = (muscle: Muscle) => {
    
  }

  const getDarkerColor = (baseColor: string) => {
    const colorValue = parseInt(baseColor.slice(1), 16);
    const r = Math.max((colorValue >> 16) - 20, 0);
    const g = Math.max(((colorValue >> 8) & 0x00ff) - 20, 0);
    const b = Math.max((colorValue & 0x0000ff) - 20, 0);
    return `#${(r << 16 | g << 8 | b).toString(16).padStart(6, '0')}`;
  };

  const baseColor = "#f1c27d";

  return (
    <div style={{ textAlign: 'center', width: '200px', margin: '0 auto' }}>
      <svg viewBox="0 0 200 400" width="200" height="400">
        {/* Голова */}
        <circle
          cx="100"
          cy="50"
          r="30"
          fill={baseColor}
          stroke="black"
          id="head"
        />

        {/* Шея */}
        <rect
          x="90"
          y="70"
          width="20"
          height="30"
          fill={highlightedMuscle === 'neck' ? getDarkerColor(baseColor) : baseColor}
          stroke="black"
          id="neck"
          onMouseEnter={() => handleMouseEnter('neck')}
          onMouseLeave={handleMouseLeave}
        />

        {/* Трапеции */}
        <path
          d="M70,100 Q100,60 130,100 L120,110 Q100,90 80,110 Z"
          fill={highlightedMuscle === 'trapezius' ? getDarkerColor(baseColor) : baseColor}
          stroke="black"
          id="trapezius"
          onMouseEnter={() => handleMouseEnter('trapezius')}
          onMouseLeave={handleMouseLeave}
        />

        {/* Грудные мышцы */}
        <path
          d="M70,100 L130,100 C135,125 135,125 130,150 Q100,170 70,150 C65,125 65,125 70,100 Z"
          fill={highlightedMuscle === 'chest' ? getDarkerColor(baseColor) : baseColor}
          stroke="black"
          id="chest"
          onMouseEnter={() => handleMouseEnter('chest')}
          onMouseLeave={handleMouseLeave}
        />

        {/* Плечи */}
        <path
          d="M70,100 L60,120 L70,130 L80,110 Z"
          fill={highlightedMuscle === 'shoulders' ? getDarkerColor(baseColor) : baseColor}
          stroke="black"
          id="leftShoulder"
          onMouseEnter={() => handleMouseEnter('shoulders')}
          onMouseLeave={handleMouseLeave}
        />
        <path
          d="M130,100 L140,120 L130,130 L120,110 Z"
          fill={highlightedMuscle === 'shoulders' ? getDarkerColor(baseColor) : baseColor}
          stroke="black"
          id="rightShoulder"
          onMouseEnter={() => handleMouseEnter('shoulders')}
          onMouseLeave={handleMouseLeave}
        />

        {/* Бицепсы */}
        <g transform="rotate(25,60,130)">
          <rect
            x="55"
            y="125"
            width="15"
            height="35"
            rx="5"
            ry="5"
            fill={highlightedMuscle === 'biceps' ? getDarkerColor(baseColor) : baseColor}
            stroke="black"
            id="leftBicep"
            onMouseEnter={() => handleMouseEnter('biceps')}
            onMouseLeave={handleMouseLeave}
          />
        </g>
        <g transform="rotate(-25,140,130)">
          <rect
            x="130"
            y="125"
            width="15"
            height="35"
            rx="5"
            ry="5"
            fill={highlightedMuscle === 'biceps' ? getDarkerColor(baseColor) : baseColor}
            stroke="black"
            id="rightBicep"
            onMouseEnter={() => handleMouseEnter('biceps')}
            onMouseLeave={handleMouseLeave}
          />
        </g>

        {/* Предплечья */}
        <g transform="rotate(25,60,130)">
          <rect
            x="55"
            y="160"
            width="15"
            height="35"
            rx="5"
            ry="5"
            fill={highlightedMuscle === 'forearms' ? getDarkerColor(baseColor) : baseColor}
            stroke="black"
            id="leftForearm"
            onMouseEnter={() => handleMouseEnter('forearms')}
            onMouseLeave={handleMouseLeave}
          />
        </g>
        <g transform="rotate(-25,140,130)">
          <rect
            x="130"
            y="160"
            width="15"
            height="35"
            rx="5"
            ry="5"
            fill={highlightedMuscle === 'forearms' ? getDarkerColor(baseColor) : baseColor}
            stroke="black"
            id="rightForearm"
            onMouseEnter={() => handleMouseEnter('forearms')}
            onMouseLeave={handleMouseLeave}
          />
        </g>

        {/* Пресс */}
        <path
          d="M70,150 L130,150 L130,210 Q100,250 70,210 Z"
          fill={highlightedMuscle === 'abs' ? getDarkerColor(baseColor) : baseColor}
          stroke="black"
          id="abs"
          onMouseEnter={() => handleMouseEnter('abs')}
          onMouseLeave={handleMouseLeave}
        />

        {/* Квадрицепсы */}
        <g transform="rotate(5,75,260)">
          <ellipse
            cx="75"
            cy="260"
            rx="15"
            ry="35"
            fill={highlightedMuscle === 'quadriceps' ? getDarkerColor(baseColor) : baseColor}
            stroke="black"
            id="leftQuadricep"
            onMouseEnter={() => handleMouseEnter('quadriceps')}
            onMouseLeave={handleMouseLeave}
          />
        </g>
        <g transform="rotate(-5,125,260)">
          <ellipse
            cx="125"
            cy="260"
            rx="15"
            ry="35"
            fill={highlightedMuscle === 'quadriceps' ? getDarkerColor(baseColor) : baseColor}
            stroke="black"
            id="rightQuadricep"
            onMouseEnter={() => handleMouseEnter('quadriceps')}
            onMouseLeave={handleMouseLeave}
          />
        </g>

        {/* Икроножные мышцы */}
        <g transform="rotate(5,75,260)">
          <ellipse
            cx="75"
            cy="325"
            rx="12"
            ry="30"
            fill={highlightedMuscle === 'calves' ? getDarkerColor(baseColor) : baseColor}
            stroke="black"
            id="leftCalf"
            onMouseEnter={() => handleMouseEnter('calves')}
            onMouseLeave={handleMouseLeave}
          />
        </g>
        <g transform="rotate(-5,125,260)">
          <ellipse
            cx="125"
            cy="325"
            rx="12"
            ry="30"
            fill={highlightedMuscle === 'calves' ? getDarkerColor(baseColor) : baseColor}
            stroke="black"
            id="rightCalf"
            onMouseEnter={() => handleMouseEnter('calves')}
            onMouseLeave={handleMouseLeave}
          />
        </g>
      </svg>

      {/* Отображение названия мышечной группы */}
      <div style={{ marginTop: '20px', fontSize: '18px' }}>
        {highlightedMuscle
          ? `Выделено: ${highlightedMuscle}`
          : 'Наведите на мышцу, чтобы увидеть название'}
      </div>
    </div>
  );
};

export default MuscleDiagram;
