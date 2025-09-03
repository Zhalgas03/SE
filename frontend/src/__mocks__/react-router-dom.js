jest.mock('react-router-dom'); // подтянет src/__mocks__/react-router-dom.js

const React = require('react');

module.exports = {
  BrowserRouter: ({ children }) => <div data-testid="router">{children}</div>,
  MemoryRouter: ({ children }) => <div data-testid="memory-router">{children}</div>,
  Routes: ({ children }) => <div data-testid="routes">{children}</div>,
  Route: ({ element }) => element || null,
  Link: ({ to = '#', children }) => <a href={to}>{children}</a>,
  Navigate: ({ to }) => <div data-testid="navigate">NAVIGATE:{to}</div>,
  Outlet: () => <div data-testid="outlet" />,
  useNavigate: () => jest.fn(),
  useLocation: () => ({ pathname: '/' }),
  useParams: () => ({}),
};
