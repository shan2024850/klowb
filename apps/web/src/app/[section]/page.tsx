import { notFound } from "next/navigation";
import { sections } from "../../lib/sections";
export default async function Page({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  const entry = sections.find(([, slug]) => slug === section);
  if (!entry) notFound();
  return <><h1>{entry[0]}</h1><section><p>This area is planned for a later phase.</p></section></>;
}
