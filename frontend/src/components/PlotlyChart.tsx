import React, { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';

interface PlotlyChartProps {
  data: any[];
  layout?: Record<string, any>;
  height?: number;
}

export const PlotlyChart: React.FC<PlotlyChartProps> = ({ data, layout = {}, height = 270 }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const mergedLayout = {
      paper_bgcolor: '#111419',
      plot_bgcolor: '#0d1015',
      font: { color: '#94a3b8', family: 'Inter, system-ui, sans-serif', size: 11 },
      margin: { t: 32, r: 16, b: 36, l: 48 },
      height,
      xaxis: {
        gridcolor: '#1e2631',
        zerolinecolor: '#232a35',
        title: { font: { size: 11, color: '#94a3b8' } },
      },
      yaxis: {
        gridcolor: '#1e2631',
        zerolinecolor: '#232a35',
        title: { font: { size: 11, color: '#94a3b8' } },
      },
      legend: {
        orientation: 'h',
        y: 1.12,
        x: 0,
        font: { size: 10, color: '#cbd5e1' },
      },
      ...layout,
    };

    Plotly.react(el, data, mergedLayout, { responsive: true, displayModeBar: false });
  }, [data, layout, height]);

  useEffect(() => {
    const el = containerRef.current;
    return () => {
      if (el) Plotly.purge(el);
    };
  }, []);

  return <div ref={containerRef} className="w-full" style={{ minHeight: height }} />;
};
