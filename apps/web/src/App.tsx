import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Dashboard } from './routes/Dashboard';
import { Documents } from './routes/Documents';
import { Review } from './routes/Review';
import { TaxPayment } from './routes/TaxPayment';
import { NotFound } from './routes/NotFound';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <Router>
          <div className="min-h-screen bg-gray-50">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/documents/:returnId" element={<Documents />} />
              <Route path="/review/:returnId" element={<Review />} />
              <Route path="/tax-payment/:returnId" element={<TaxPayment />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </div>
        </Router>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;