import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Button, HashBadge, Input, OtpInput, ToastProvider } from './index';

afterEach(() => vi.restoreAllMocks());

describe('Button', () => {
  it('supports disabled and loading actions', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<><Button disabled onClick={onClick}>Save</Button><Button loading>Saving</Button></>);
    await user.click(screen.getByRole('button', { name: 'Save' }));
    const loadingButton = screen.getByRole('button', { name: 'Saving' });
    expect(onClick).not.toHaveBeenCalled();
    expect(loadingButton).toBeDisabled();
    expect(loadingButton).toHaveAttribute('aria-busy', 'true');
  });
});

describe('Input', () => {
  it('connects the inline error to the field', () => {
    render(<Input label="Case title" name="title" required error="A title is required" />);
    const input = screen.getByRole('textbox', { name: /Case title/ });
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAccessibleDescription('A title is required');
  });
});

describe('OtpInput', () => {
  it('accepts pasted codes and advances focus when typing', () => {
    const onChange = vi.fn();
    const { rerender } = render(<OtpInput value="" onChange={onChange} />);
    const first = screen.getByRole('textbox', { name: 'One-time code digit 1' });
    fireEvent.paste(first, { clipboardData: { getData: () => '123456' } });
    expect(onChange).toHaveBeenLastCalledWith('123456');

    rerender(<OtpInput value="1" onChange={onChange} />);
    fireEvent.change(screen.getByRole('textbox', { name: 'One-time code digit 1' }), { target: { value: '2' } });
    expect(onChange).toHaveBeenLastCalledWith('2');
    expect(screen.getByRole('textbox', { name: 'One-time code digit 2' })).toHaveFocus();
  });
});

describe('HashBadge', () => {
  it('copies the full hash and confirms the action', async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });
    render(<ToastProvider><HashBadge hash="123456789012345678901234" /></ToastProvider>);
    expect(screen.getByText('12345678…901234')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Copy value' }));
    expect(writeText).toHaveBeenCalledWith('123456789012345678901234');
    expect(await screen.findByText('Copied')).toBeInTheDocument();
  });
});
