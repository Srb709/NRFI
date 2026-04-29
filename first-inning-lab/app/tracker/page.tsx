import Shell from '@/components/Shell';import {getResults} from '@/lib/local-store';import TrackerTable from '@/components/TrackerTable';
export default async function Page(){const rows=await getResults();return <Shell><h1 className='text-3xl mb-4'>Public Record Tracker (Demo)</h1><TrackerTable rows={rows as any}/></Shell>}
