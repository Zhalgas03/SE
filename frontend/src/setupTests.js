import '@testing-library/jest-dom';

// 1) jsdom не умеет canvas → заглушка
Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
  value: () => ({
    fillRect: () => {},
    drawImage: () => {},
    getImageData: () => ({ data: new Uint8ClampedArray() }),
    putImageData: () => {},
    createImageData: () => ({}),
    measureText: () => ({ width: 0 }),
    clearRect: () => {},
  }),
});

// 2) тяжёлые браузерные либы → моки
jest.mock('jspdf', () =>
  jest.fn().mockImplementation(() => ({
    addImage: jest.fn(),
    text: jest.fn(),
    save: jest.fn(),
  }))
);

jest.mock('html2canvas', () =>
  jest.fn().mockResolvedValue({
    toDataURL: () => 'data:image/png;base64,AAA',
  })
);

jest.mock('react-confetti', () => () => null);

jest.mock('@react-hook/window-size', () => ({
  useWindowSize: () => [1024, 768],
  useWindowWidth: () => 1024,
  useWindowHeight: () => 768,
}));

// 3) подключаем ручной мок axios из src/__mocks__/axios.js
jest.mock('axios');
