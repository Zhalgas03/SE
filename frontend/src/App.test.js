jest.mock('react-router-dom');

import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';
import { UserProvider } from './context/UserContext';

jest.mock('./components/Navbar', () => () => <nav data-testid="navbar">Navbar</nav>);
jest.mock('./pages/PlannerPage', () => () => <div data-testid="planner">Planner</div>);
jest.mock('./pages/Success', () => () => <div data-testid="success">Success</div>);

test('smoke: App renders with router and navbar', () => {
  render(
    <UserProvider>
      <App />
    </UserProvider>
  );
  expect(screen.getByTestId('navbar')).toBeInTheDocument();
});
