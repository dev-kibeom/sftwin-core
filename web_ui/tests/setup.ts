import '@testing-library/jest-dom';
import 'vitest-canvas-mock';

global.ResizeObserver = class ResizeObserver {
    observe() { }
    unobserve() { }
    disconnect() { }
};

window.WebGLRenderingContext = window.WebGLRenderingContext || {};
