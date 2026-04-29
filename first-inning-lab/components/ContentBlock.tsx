import CopyButton from './CopyButton';

export default function ContentBlock({ title, content }: { title: string; content: string }) {
  return <section className="card"><div className="flex justify-between items-center"><h4 className="font-medium">{title}</h4><CopyButton text={content} /></div><pre className="whitespace-pre-wrap text-sm text-zinc-300 mt-3">{content}</pre></section>;
}
