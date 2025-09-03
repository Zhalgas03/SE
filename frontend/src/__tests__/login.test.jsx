// используем реальный роутер
jest.unmock('react-router-dom');

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';
import { UserProvider } from '../context/UserContext';
import axios from 'axios';

// Уберём побочки тяжёлых страниц
jest.mock('../components/Navbar', () => () => <nav data-testid="navbar">Navbar</nav>);
jest.mock('../pages/PlannerPage', () => () => <div data-testid="planner" />);
jest.mock('../pages/Success', () => () => <div data-testid="success" />);
jest.mock('../pages/AccountPage', () => () => <div data-testid="account" />);
jest.mock('../pages/VotePage', () => () => <div data-testid="vote" />);

test('login route renders and submits credentials', async () => {
  // Переходим на /login ДО рендера (чтобы BrowserRouter в App прочитал URL)
  window.history.pushState({}, '', '/login');

  // Успешный ответ логина
  axios.post.mockResolvedValueOnce({
    data: { success: true, token: 'fake-jwt' },
  });

  render(
    <UserProvider>
      <App />
    </UserProvider>
  );

  // Найдём поля (подгони селекторы под свою верстку, если нужно)
  const emailInput =
    screen.queryByLabelText(/email/i) || screen.getByPlaceholderText(/email/i);
  const passwordInput =
    screen.queryByLabelText(/password/i) || screen.getByPlaceholderText(/password/i);
  const submitBtn =
    screen.queryByRole('button', { name: /log ?in|sign ?in/i }) ||
    screen.getByRole('button');

  await userEvent.type(emailInput, 'test@example.com');
  await userEvent.type(passwordInput, 'secret123');
  await userEvent.click(submitBtn);

  await waitFor(() => expect(axios.post).toHaveBeenCalled());

  const [url, body] = axios.post.mock.calls[0];
  expect(url).toMatch(/login/i); // например /api/login
  expect(body).toEqual(
    expect.objectContaining({ email: 'test@example.com', password: 'secret123' })
  );
});
