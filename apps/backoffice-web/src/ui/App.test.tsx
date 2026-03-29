import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';
import { BackofficeApi } from './backofficeApi';

describe('Backoffice App', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    cleanup();
    window.history.replaceState({}, '', '/');
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('shows only barista tabs for barista session', async () => {
    window.history.replaceState({}, '', '/?preview=1&role=barista');

    render(<App api={new BackofficeApi()} />);

    expect((await screen.findAllByRole('button', { name: 'Заказы' })).length).toBeGreaterThan(0);
    expect(screen.getAllByRole('button', { name: 'Доступность' }).length).toBeGreaterThan(0);
    expect(screen.queryAllByRole('button', { name: 'Меню' })).toHaveLength(0);
    expect(screen.queryAllByRole('button', { name: 'Пользователи' })).toHaveLength(0);
    expect(screen.queryAllByRole('button', { name: 'Настройки' })).toHaveLength(0);
  });

  it('requires a reject reason before submitting the dialog', async () => {
    window.history.replaceState({}, '', '/?preview=1');

    render(<App api={new BackofficeApi()} />);

    await userEvent.click(await screen.findByRole('button', { name: 'Отклонить' }));
    await userEvent.click(screen.getByRole('button', { name: 'Подтвердить отказ' }));

    expect(await screen.findByText('Укажите причину отказа, чтобы закрыть диалог.')).toBeInTheDocument();
  });

  it('validates working hours before saving settings', async () => {
    window.history.replaceState({}, '', '/?preview=1');

    render(<App api={new BackofficeApi()} />);

    const settingsButtons = await screen.findAllByRole('button', { name: 'Настройки' });
    await userEvent.click(settingsButtons[0]);

    const openingInput = await screen.findByLabelText('Открытие');
    const closingInput = screen.getByLabelText('Закрытие');

    await userEvent.clear(openingInput);
    await userEvent.type(openingInput, '22:00');
    await userEvent.clear(closingInput);
    await userEvent.type(closingInput, '08:00');
    await userEvent.click(screen.getByRole('button', { name: 'Сохранить' }));

    expect(await screen.findByText('Время открытия должно быть раньше времени закрытия.')).toBeInTheDocument();
  });

  it('falls back to mock mode when live backoffice API is unavailable', async () => {
    vi.mocked(global.fetch).mockRejectedValue(new Error('ECONNREFUSED'));

    render(<App api={new BackofficeApi()} />);

    expect(await screen.findByText('Expressa Backoffice')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Операционный пульт смены')).toBeInTheDocument());
  });
});
