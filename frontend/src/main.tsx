import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource-variable/source-serif-4';
import '@fontsource/jetbrains-mono/400.css';
import './styles/tokens.css';
import './styles/globals.css';
import './styles/print.css';
import { QueryClientProvider } from '@tanstack/react-query';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { queryClient } from './api/keys';
import { ThemeProvider } from './theme/ThemeProvider';
import { ToastProvider, TooltipProvider } from './components/ui';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <ToastProvider>
            <BrowserRouter><App/></BrowserRouter>
          </ToastProvider>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>,
);
