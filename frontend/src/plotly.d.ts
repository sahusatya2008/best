declare module 'plotly.js-dist-min' {
  const Plotly: {
    newPlot: (root: HTMLElement | string, data: any[], layout?: any, config?: any) => Promise<any>;
    react: (root: HTMLElement | string, data: any[], layout?: any, config?: any) => Promise<any>;
    purge: (root: HTMLElement) => void;
  };
  export default Plotly;
}
