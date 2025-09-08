// src/__mocks__/axios.js
const mock = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    patch: jest.fn(),
    head: jest.fn(),
    // axios.create() должен возвращать сам мок
    create: jest.fn(() => mock),
  };
  
  export default mock;
  export const get = mock.get;
  export const post = mock.post;
  export const put = mock.put;
  export const del = mock.delete;
  export const patch = mock.patch;
  export const head = mock.head;
  export const create = mock.create;
  