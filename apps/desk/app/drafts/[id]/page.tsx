import DeskApp from "../../../components/DeskApp";

export default async function DraftPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <DeskApp initialId={id} />;
}
