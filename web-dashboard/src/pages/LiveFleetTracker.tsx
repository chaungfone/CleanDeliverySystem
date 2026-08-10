import { useMemo } from 'react';
import { MapPin, Navigation, User } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { Driver } from '../lib/types';
import { ErrorState, LoadingState, asArray, formatTime } from '../lib/ui';
import { useI18n } from '../i18n';

const DEFAULT_CENTER: [number, number] = [16.8409, 96.1735];

function toCoords(location: unknown): [number, number] | null {
  if (!location) return null;
  if (typeof location === 'object') {
    const obj = location as { coordinates?: [number, number] | null };
    if (Array.isArray(obj.coordinates) && obj.coordinates.length === 2) {
      const [lon, lat] = obj.coordinates;
      return [lat, lon];
    }
  }
  if (typeof location === 'string') {
    if (location.startsWith('{')) {
      try {
        const parsed = JSON.parse(location) as { coordinates?: [number, number] | null };
        if (Array.isArray(parsed.coordinates) && parsed.coordinates.length === 2) {
          const [lon, lat] = parsed.coordinates;
          return [lat, lon];
        }
      } catch {
        // not valid GeoJSON string
      }
    }
  }
  return null;
}

export default function LiveFleetTracker() {
  const { t } = useI18n();
  const driversQuery = useQuery({
    queryKey: ['admin', 'drivers'],
    queryFn: () => apiFetch<Driver[]>('/admin/drivers'),
  });

  const drivers = useMemo(() => {
    const list = asArray<Driver>(driversQuery.data);
    return list.map((driver) => ({ ...driver, coords: toCoords(driver.location) }));
  }, [driversQuery.data]);

  const withLocation = drivers.filter((d) => d.coords);

  if (driversQuery.isLoading) return <LoadingState label={t('common.loading')} />;
  if (driversQuery.isError) {
    return <ErrorState error={driversQuery.error} fallback={t('errors.failedToLoad')} />;
  }

  const inTransit = drivers.filter((d) => d.last_ping).length;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-neutral-900">{t('fleet.title')}</h2>
          <p className="text-neutral-500 text-sm mt-0.5">{t('fleet.subtitle')}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <StatusCount label={t('fleet.drivers')} count={drivers.length} color="bg-green-500" />
          <StatusCount label={t('fleet.withLocation')} count={withLocation.length} color="bg-primary-500" />
          <StatusCount label={t('fleet.lastPing')} count={inTransit} color="bg-orange-400" />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        <div className="xl:col-span-3 rounded-2xl overflow-hidden relative border border-neutral-90 shadow-card min-h-[420px] bg-neutral-90">
          {withLocation.length > 0 ? (
            <MapContainer center={withLocation[0].coords ?? DEFAULT_CENTER} zoom={12} className="w-full h-full min-h-[420px]">
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              {withLocation.map((driver) => (
                <Marker key={driver.id} position={driver.coords!}>
                  <Popup>
                    <b>{driver.full_name}</b>
                    <br />
                    <span className="text-xs">{formatTime(driver.last_ping)}</span>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-neutral-400 font-medium">
              <div className="text-center px-4">
                <Navigation className="w-12 h-12 mx-auto mb-4 animate-pulse" />
                <p>{t('fleet.noLocations')}</p>
                <p className="text-xs mt-1">{t('fleet.noLocationsHint')}</p>
              </div>
            </div>
          )}
        </div>

        <div className="card flex flex-col">
          <div className="p-4 border-b border-neutral-90">
            <h3 className="font-bold text-neutral-900">
              {t('fleet.driversCount')} ({drivers.length})
            </h3>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-[420px] xl:max-h-none">
            {drivers.length === 0 && (
              <p className="text-sm text-neutral-400 text-center py-8">{t('fleet.noDrivers')}</p>
            )}
            {drivers.map((driver) => (
              <DriverTrackerCard
                key={driver.id}
                name={driver.full_name}
                status={driver.last_ping ? t('fleet.activeStatus') : t('fleet.noLocationStatus')}
                isActive={Boolean(driver.last_ping)}
                lastPing={formatTime(driver.last_ping)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusCount({ label, count, color }: any) {
  return (
    <div className="flex items-center gap-2 card px-3 py-1.5">
      <span className={`w-2 h-2 rounded-full ${color}`} />
      <span className="text-sm font-bold text-neutral-600">{count}</span>
      <span className="text-xs text-neutral-400 font-medium">{label}</span>
    </div>
  );
}

function DriverTrackerCard({ name, status, isActive, lastPing }: any) {
  return (
    <div className="p-3 rounded-xl border border-neutral-90 bg-neutral-99 hover:border-primary-200 hover:bg-primary-50/60 transition-all cursor-pointer group">
      <div className="flex items-center justify-between mb-2">
        <span className="font-bold text-sm text-neutral-800">{name}</span>
        <span
          className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold uppercase ${
            isActive ? 'bg-primary-100 text-primary-700' : 'bg-neutral-90 text-neutral-500'
          }`}
        >
          {status}
        </span>
      </div>
      <div className="flex items-center justify-between text-[10px] text-neutral-400 font-medium">
        <div className="flex items-center gap-1">
          <MapPin className="w-3 h-3" />
          {lastPing}
        </div>
        <User className="w-3 h-3" />
      </div>
    </div>
  );
}
