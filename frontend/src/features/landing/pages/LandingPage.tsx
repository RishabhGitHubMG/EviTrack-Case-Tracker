import { useDocumentMeta } from '../../../hooks/useDocumentMeta';
import { Hero } from '../components/Hero';
import { FeaturesGrid, FinalCta, HowItWorks, ProblemSolution, SecurityBand, TrustStrip } from '../components/LandingSections';

const title = 'EviTrack | Digital evidence and case tracking';
const description = 'Manage cases, SHA-256 verified evidence, chain of custody, hearings and reminders in one secure place for small law firms and police stations.';

export default function LandingPage() {
  useDocumentMeta({ title, description });
  return (
    <>
      <Hero />
      <TrustStrip />
      <ProblemSolution />
      <FeaturesGrid />
      <HowItWorks />
      <SecurityBand />
      <FinalCta />
    </>
  );
}
