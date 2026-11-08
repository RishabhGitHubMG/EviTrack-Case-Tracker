import { useState } from 'react';
import { ThemeProvider, useTheme } from './theme/ThemeProvider';
import {
  Avatar,
  Badge,
  Button,
  Card,
  Checkbox,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  EmptyState,
  ErrorState,
  HashBadge,
  Input,
  OtpInput,
  PasswordStrength,
  Pill,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
  Switch,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Textarea,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './components/ui';

function Showcase() {
  const { theme, toggleTheme } = useTheme();
  const [otp, setOtp] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  return <main className="design-page">
    <header className="design-page__header"><div><span className="eyebrow">EviTrack foundations</span><h1>Design system</h1><p>Core interface components in light and dark themes.</p></div><Button variant="secondary" onClick={toggleTheme}>Switch to {theme === 'dark' ? 'light' : 'dark'} mode</Button></header>
    <div className="design-grid">
      <Card><h2>Buttons and status</h2><div className="component-row"><Button>Primary action</Button><Button variant="accent">Accent</Button><Button variant="secondary">Secondary</Button><Button variant="danger">Danger</Button><Button variant="ghost">Ghost</Button></div><div className="component-row"><Badge>Evidence</Badge><Pill value="Verified"/><Pill value="Pending"/><Pill value="Modified"/><Avatar name="Meera Sharma"/></div></Card>
      <Card><h2>Fields</h2><div className="component-stack"><Input label="Email" placeholder="name@example.test"/><Input label="Case title" value="A sample case" readOnly error="Example validation message"/><Textarea label="Description" placeholder="Add a short description"/><Select defaultValue="investigator"><SelectTrigger aria-label="Requested role"><SelectValue/></SelectTrigger><SelectContent><SelectItem value="investigator">Investigator</SelectItem><SelectItem value="custodian">Evidence Custodian</SelectItem></SelectContent></Select></div></Card>
      <Card><h2>Controls</h2><div className="component-row"><div className="inline-control"><Checkbox aria-label="Accept terms"/><span>Accept terms</span></div><div className="inline-control"><span>Dark mode</span><Switch aria-label="Toggle dark mode" checked={theme === 'dark'} onCheckedChange={toggleTheme}/></div><DropdownMenu><DropdownMenuTrigger asChild><Button variant="secondary">More actions</Button></DropdownMenuTrigger><DropdownMenuContent align="start"><DropdownMenuItem>Open case</DropdownMenuItem><DropdownMenuItem>View audit</DropdownMenuItem></DropdownMenuContent></DropdownMenu><Dialog open={dialogOpen} onOpenChange={setDialogOpen}><DialogTrigger asChild><Button variant="secondary">Open dialog</Button></DialogTrigger><DialogContent><DialogTitle>Confirm action</DialogTitle><DialogDescription>This is an accessible dialog preview.</DialogDescription><Button onClick={() => setDialogOpen(false)}>Done</Button></DialogContent></Dialog></div></Card>
      <Card><h2>Feedback and identity</h2><div className="component-stack"><Skeleton className="skeleton-line"/><EmptyState title="No records yet" description="New items will appear here."/><ErrorState title="Unable to load" description="Try again when your connection is restored."/><TooltipProvider><Tooltip><TooltipTrigger asChild><Button variant="ghost">What is SHA-256?</Button></TooltipTrigger><TooltipContent>A unique fingerprint calculated from a file.</TooltipContent></Tooltip></TooltipProvider><HashBadge hash="ae21d6ab0052f6f87c36a10a343d3282ae21d6ab0052f6f87c36"/></div></Card>
      <Card><h2>Access inputs</h2><div className="component-stack"><PasswordStrength password="Evidence#2026"/><OtpInput value={otp} onChange={setOtp}/><p className="field-help">Entered {otp.length} of 6 digits.</p></div></Card>
      <Card><h2>Tabs</h2><Tabs defaultValue="overview"><TabsList><TabsTrigger value="overview">Overview</TabsTrigger><TabsTrigger value="history">History</TabsTrigger></TabsList><TabsContent value="overview">Case overview content</TabsContent><TabsContent value="history">Audit history content</TabsContent></Tabs></Card>
    </div>
  </main>;
}

export default function DesignPage() {
  if (!import.meta.env.DEV) return <main className="design-page"><h1>Not found</h1></main>;
  return <ThemeProvider><TooltipProvider><Showcase/></TooltipProvider></ThemeProvider>;
}
