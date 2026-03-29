import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';
import { CustomerApi } from './customerApi';

describe('Customer App', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    cleanup();
    window.localStorage.clear();
    window.history.replaceState({}, '', '/');
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('shows blocked state for blocked customers', async () => {
    window.history.replaceState({}, '', '/?preview=1&state=blocked');

    render(<App api={new CustomerApi()} />);

    expect(await screen.findByText('Доступ временно недоступен')).toBeInTheDocument();
  });

  it('requires size selection before adding to cart', async () => {
    window.history.replaceState({}, '', '/?preview=1');

    render(<App api={new CustomerApi()} />);

    const [openButton] = await screen.findAllByRole('button', { name: 'Настроить' });
    await userEvent.click(openButton);

    const addButton = await screen.findByRole('button', { name: 'Добавить в корзину' });
    expect(addButton).toBeDisabled();

    await userEvent.click(screen.getByRole('button', { name: /S \/ 250 мл/i }));
    await waitFor(() => expect(addButton).toBeEnabled());
  });

  it('falls back to mock mode when live customer API is unavailable', async () => {
    vi.mocked(global.fetch).mockRejectedValue(new Error('ECONNREFUSED'));

    render(<App api={new CustomerApi()} />);

    expect(await screen.findByText('Expressa Customer')).toBeInTheDocument();
    expect((await screen.findAllByRole('button', { name: 'Настроить' })).length).toBeGreaterThan(0);
  });
});
