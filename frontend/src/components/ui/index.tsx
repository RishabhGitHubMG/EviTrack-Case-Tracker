import * as DialogPrimitive from '@radix-ui/react-dialog';
import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu';
import * as SelectPrimitive from '@radix-ui/react-select';
import * as SwitchPrimitive from '@radix-ui/react-switch';
import * as TabsPrimitive from '@radix-ui/react-tabs';
import * as ToastPrimitive from '@radix-ui/react-toast';
import * as TooltipPrimitive from '@radix-ui/react-tooltip';
import { Check, ChevronDown, CircleAlert, Copy, X } from 'lucide-react';
import {
  createContext,
  forwardRef,
  useContext,
  useRef,
  useState,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type TextareaHTMLAttributes,
} from 'react';

const cn = (...values: Array<string | undefined | false>) => values.filter(Boolean).join(' ');

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'accent' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = 'primary', size = 'md', ...props },
  ref,
) {
  return <button ref={ref} className={cn('ui-button', `ui-button--${variant}`, `ui-button--${size}`, className)} {...props} />;
});

export type InputProps = InputHTMLAttributes<HTMLInputElement> & { label?: string; error?: string };

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { id, label, error, className, ...props },
  ref,
) {
  const inputId = id ?? props.name;
  const errorId = error && inputId ? `${inputId}-error` : undefined;
  return (
    <label className="ui-field" htmlFor={inputId}>
      {label && <span className="ui-field__label">{label}</span>}
      <input ref={ref} id={inputId} className={cn('ui-input', error && 'ui-input--error', className)} aria-invalid={Boolean(error)} aria-describedby={errorId} {...props} />
      {error && <span className="ui-field__error" id={errorId}><CircleAlert size={14} aria-hidden="true" />{error}</span>}
    </label>
  );
});

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string; error?: string };

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { id, label, error, className, ...props },
  ref,
) {
  const inputId = id ?? props.name;
  const errorId = error && inputId ? `${inputId}-error` : undefined;
  return (
    <label className="ui-field" htmlFor={inputId}>
      {label && <span className="ui-field__label">{label}</span>}
      <textarea ref={ref} id={inputId} className={cn('ui-input ui-textarea', error && 'ui-input--error', className)} aria-invalid={Boolean(error)} aria-describedby={errorId} {...props} />
      {error && <span className="ui-field__error" id={errorId}><CircleAlert size={14} aria-hidden="true" />{error}</span>}
    </label>
  );
});

export const Select = SelectPrimitive.Root;
export const SelectGroup = SelectPrimitive.Group;
export const SelectValue = SelectPrimitive.Value;
export const SelectTrigger = forwardRef<
  React.ElementRef<typeof SelectPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>
>(function SelectTrigger({ className, children, ...props }, ref) {
  return <SelectPrimitive.Trigger ref={ref} className={cn('ui-select', className)} {...props}>{children}<SelectPrimitive.Icon><ChevronDown size={16} /></SelectPrimitive.Icon></SelectPrimitive.Trigger>;
});
export const SelectContent = forwardRef<
  React.ElementRef<typeof SelectPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Content>
>(function SelectContent({ className, children, position = 'popper', ...props }, ref) {
  return <SelectPrimitive.Portal><SelectPrimitive.Content ref={ref} position={position} className={cn('ui-select__content', className)} {...props}><SelectPrimitive.Viewport>{children}</SelectPrimitive.Viewport></SelectPrimitive.Content></SelectPrimitive.Portal>;
});
export const SelectItem = forwardRef<
  React.ElementRef<typeof SelectPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Item>
>(function SelectItem({ className, children, ...props }, ref) {
  return <SelectPrimitive.Item ref={ref} className={cn('ui-select__item', className)} {...props}><SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText><SelectPrimitive.ItemIndicator><Check size={14} /></SelectPrimitive.ItemIndicator></SelectPrimitive.Item>;
});

export const Checkbox = forwardRef<HTMLInputElement, Omit<InputHTMLAttributes<HTMLInputElement>, 'type'>>(function Checkbox(
  { className, ...props },
  ref,
) {
  return <input ref={ref} type="checkbox" className={cn('ui-checkbox', className)} {...props} />;
});

export const Switch = forwardRef<
  React.ElementRef<typeof SwitchPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitive.Root>
>(function Switch({ className, ...props }, ref) {
  return <SwitchPrimitive.Root ref={ref} className={cn('ui-switch', className)} {...props}><SwitchPrimitive.Thumb className="ui-switch__thumb" /></SwitchPrimitive.Root>;
});

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('ui-card', className)} {...props} />;
}

export function Badge({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return <span className={cn('ui-badge', className)} {...props} />;
}

export function Pill({ value, className, ...props }: React.HTMLAttributes<HTMLSpanElement> & { value: string }) {
  return <Badge className={cn('ui-pill', `ui-pill--${value.toLowerCase().replaceAll(' ', '-')}`, className)} {...props}>{value}</Badge>;
}

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('ui-skeleton', className)} aria-hidden="true" {...props} />;
}

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return <section className="ui-state" aria-label={title}><span className="ui-state__icon" aria-hidden="true">—</span><h2>{title}</h2>{description && <p>{description}</p>}{action}</section>;
}

export function ErrorState({ title = 'Something went wrong', description = 'Please try again.', onRetry }: { title?: string; description?: string; onRetry?: () => void }) {
  return <section className="ui-state ui-state--error" role="alert"><CircleAlert aria-hidden="true" /><h2>{title}</h2><p>{description}</p>{onRetry && <Button variant="secondary" onClick={onRetry}>Try again</Button>}</section>;
}

export const TooltipProvider = TooltipPrimitive.Provider;
export const Tooltip = TooltipPrimitive.Root;
export const TooltipTrigger = TooltipPrimitive.Trigger;
export const TooltipContent = forwardRef<
  React.ElementRef<typeof TooltipPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>
>(function TooltipContent({ className, sideOffset = 5, ...props }, ref) {
  return <TooltipPrimitive.Portal><TooltipPrimitive.Content ref={ref} className={cn('ui-tooltip', className)} sideOffset={sideOffset} {...props} /></TooltipPrimitive.Portal>;
});

const ToastContext = createContext<(message: string, kind?: 'success' | 'error' | 'info') => void>(() => undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Array<{ id: number; message: string; kind: string }>>([]);
  const nextId = useRef(0);
  const toast = (message: string, kind: 'success' | 'error' | 'info' = 'info') => {
    const id = ++nextId.current;
    setItems((current) => [...current, { id, message, kind }]);
  };
  return (
    <ToastContext.Provider value={toast}>
      <ToastPrimitive.Provider duration={4000}>
        {children}
        {items.map((item) => <ToastPrimitive.Root key={item.id} className={cn('ui-toast', `ui-toast--${item.kind}`)} onOpenChange={(open) => !open && setItems((current) => current.filter((entry) => entry.id !== item.id))}><ToastPrimitive.Title>{item.message}</ToastPrimitive.Title><ToastPrimitive.Close aria-label="Close notification"><X size={16} /></ToastPrimitive.Close></ToastPrimitive.Root>)}
        <ToastPrimitive.Viewport className="ui-toast-viewport" />
      </ToastPrimitive.Provider>
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;
export const DialogPortal = DialogPrimitive.Portal;
export const DialogOverlay = forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(function DialogOverlay({ className, ...props }, ref) {
  return <DialogPrimitive.Overlay ref={ref} className={cn('ui-dialog__overlay', className)} {...props} />;
});
export const DialogContent = forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(function DialogContent({ className, children, ...props }, ref) {
  return <DialogPortal><DialogOverlay /><DialogPrimitive.Content ref={ref} className={cn('ui-dialog__content', className)} {...props}>{children}<DialogPrimitive.Close className="ui-dialog__close" aria-label="Close"><X size={18} /></DialogPrimitive.Close></DialogPrimitive.Content></DialogPortal>;
});
export const DialogTitle = DialogPrimitive.Title;
export const DialogDescription = DialogPrimitive.Description;

export function ConfirmDialog({ open, onOpenChange, title, description, onConfirm }: { open: boolean; onOpenChange: (open: boolean) => void; title: string; description: string; onConfirm: () => void }) {
  return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><DialogTitle>{title}</DialogTitle><DialogDescription>{description}</DialogDescription><div className="ui-dialog__actions"><DialogClose asChild><Button variant="secondary">Cancel</Button></DialogClose><Button variant="danger" onClick={onConfirm}>Confirm</Button></div></DialogContent></Dialog>;
}

export const DropdownMenu = DropdownMenuPrimitive.Root;
export const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger;
export const DropdownMenuItem = forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item>
>(function DropdownMenuItem({ className, ...props }, ref) {
  return <DropdownMenuPrimitive.Item ref={ref} className={cn('ui-dropdown__item', className)} {...props} />;
});
export const DropdownMenuContent = forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content>
>(function DropdownMenuContent({ className, ...props }, ref) {
  return <DropdownMenuPrimitive.Portal><DropdownMenuPrimitive.Content ref={ref} className={cn('ui-dropdown__content', className)} {...props} /></DropdownMenuPrimitive.Portal>;
});

export const Tabs = TabsPrimitive.Root;
export const TabsList = forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(function TabsList({ className, ...props }, ref) {
  return <TabsPrimitive.List ref={ref} className={cn('ui-tabs__list', className)} {...props} />;
});
export const TabsTrigger = forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(function TabsTrigger({ className, ...props }, ref) {
  return <TabsPrimitive.Trigger ref={ref} className={cn('ui-tabs__trigger', className)} {...props} />;
});
export const TabsContent = TabsPrimitive.Content;

export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase() || '?';
  return <span className={cn('ui-avatar', className)} aria-label={name}>{initials}</span>;
}

export function CopyButton({ value, onCopy }: { value: string; onCopy?: () => void }) {
  const toast = useToast();
  const copy = async () => {
    await navigator.clipboard.writeText(value);
    onCopy?.();
    toast('Copied', 'success');
  };
  return <Button type="button" variant="ghost" size="sm" aria-label="Copy value" onClick={copy}><Copy size={15} /></Button>;
}

export function HashBadge({ hash, onCopy }: { hash: string; onCopy?: () => void }) {
  const shortHash = hash.length > 14 ? `${hash.slice(0, 8)}…${hash.slice(-6)}` : hash;
  return <span className="ui-hash"><code>{shortHash}</code><CopyButton value={hash} onCopy={onCopy} /></span>;
}

export function PasswordStrength({ password }: { password: string }) {
  const checks = [password.length >= 12, /[A-Z]/.test(password), /[a-z]/.test(password), /\d/.test(password), /[^A-Za-z0-9]/.test(password)];
  const score = checks.filter(Boolean).length;
  const label = score < 2 ? 'Weak' : score < 4 ? 'Fair' : 'Strong';
  return <div className="ui-password-strength"><div className={`ui-password-strength__bar ui-password-strength__bar--${label.toLowerCase()}`} role="meter" aria-label={`Password strength: ${label}`} aria-valuemin={0} aria-valuemax={5} aria-valuenow={score}><span style={{ width: `${score * 20}%` }} /></div><span>{label}</span><ul>{['12+ characters', 'Uppercase letter', 'Lowercase letter', 'Number', 'Symbol'].map((rule, index) => <li key={rule}><span aria-hidden="true">{checks[index] ? '✓' : '○'}</span> {rule}: {checks[index] ? 'met' : 'not met'}</li>)}</ul></div>;
}

export function OtpInput({ value, onChange, length = 6, label = 'One-time code' }: { value: string; onChange: (value: string) => void; length?: number; label?: string }) {
  const refs = useRef<Array<HTMLInputElement | null>>([]);
  const update = (next: string) => onChange(next.replace(/\D/g, '').slice(0, length));
  return <div className="ui-otp" role="group" aria-label={label} onPaste={(event) => { const pasted = event.clipboardData.getData('text').replace(/\D/g, '').slice(0, length); if (pasted) { event.preventDefault(); update(pasted); refs.current[Math.min(pasted.length, length) - 1]?.focus(); } }}>
    {Array.from({ length }, (_, index) => <input key={index} ref={(element) => { refs.current[index] = element; }} aria-label={`${label} digit ${index + 1}`} autoComplete={index === 0 ? 'one-time-code' : 'off'} inputMode="numeric" pattern="[0-9]*" maxLength={1} value={value[index] ?? ''} onChange={(event) => { const digit = event.target.value.replace(/\D/g, '').slice(-1); const next = `${value.slice(0, index)}${digit}${value.slice(index + 1)}`.slice(0, length); update(next); if (digit && index < length - 1) refs.current[index + 1]?.focus(); }} onKeyDown={(event) => { if (event.key === 'Backspace' && !value[index] && index > 0) refs.current[index - 1]?.focus(); }} />)}
  </div>;
}
