import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { en, type Messages } from './en';
import { my } from './my';

export type Lang = 'en' | 'my';

const dictionaries: Record<Lang, Messages> = { en, my };
const STORAGE_KEY = 'cd_lang';

interface I18nContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextValue | undefined>(undefined);

function resolve(obj: unknown, key: string): string | undefined {
  let current: unknown = obj;
  for (const part of key.split('.')) {
    if (current == null) return undefined;
    current = (current as Record<string, unknown>)[part];
  }
  return typeof current === 'string' ? current : undefined;
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'my' || saved === 'en') return saved;
    } catch {
      // localStorage unavailable
    }
    return 'en';
  });

  useEffect(() => {
    document.documentElement.lang = lang === 'my' ? 'my' : 'en';
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // ignore
    }
  }, [lang]);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => {
      const dict = dictionaries[lang];
      let text = resolve(dict, key);
      if (text == null) {
        text = resolve(en, key) ?? key;
      }
      if (vars) {
        for (const [k, v] of Object.entries(vars)) {
          text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
        }
      }
      return text;
    },
    [lang]
  );

  const setLang = useCallback((next: Lang) => setLangState(next), []);

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used within I18nProvider');
  return ctx;
}
