import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://wdrbfxcnjhyryuzztjcq.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndkcmJmeGNuamh5cnl1enp0amNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjc2MzM2NzUsImV4cCI6MjA0MzIwOTY3NX0.4oE7xdTRdqpx2X55l8wxGPSJAT4j4sqeAx03GByFYhs'
export const supabase = createClient(supabaseUrl, supabaseKey);