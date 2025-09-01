// En /src/lib/supabase.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://ovvwfgqkbhezcsegrdtz.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im92dndmZ3FrYmhlemNzZWdyZHR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2OTc2MTEsImV4cCI6MjA3MjI3MzYxMX0.tbptDvXyR1IvPpncCgVOx3IWD2KajJNWUsGNQQ_mGpQ'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
