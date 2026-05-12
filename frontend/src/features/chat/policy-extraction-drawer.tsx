import { Button, Drawer, Skeleton, Tag, Typography } from 'antd'
import { useTranslation } from 'react-i18next'

import type { PolicyExtraction } from '../../types/gov'

type PolicyExtractionDrawerProps = {
  open: boolean
  dark: boolean
  loading: boolean
  error: string
  data: PolicyExtraction | null
  onClose: () => void
}

export function PolicyExtractionDrawer({
  open,
  dark,
  loading,
  error,
  data,
  onClose,
}: PolicyExtractionDrawerProps) {
  const { t } = useTranslation()

  return (
    <Drawer
      open={open}
      onClose={onClose}
      width={460}
      title={t('extractionTitle')}
      className={dark ? 'gov-drawer gov-drawer-dark' : 'gov-drawer gov-drawer-light'}
    >
      {loading ? (
        <Skeleton active paragraph={{ rows: 8 }} />
      ) : error ? (
        <div className={dark ? 'rounded-2xl border border-rose-400/20 bg-rose-500/10 p-4 text-sm text-rose-200' : 'rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700'}>
          {error}
        </div>
      ) : data ? (
        <div className="space-y-5">
          <section>
            <Typography.Title level={5} className={dark ? '!mb-2 !text-[#f3f4f6]' : '!mb-2 !text-[#111827]'}>
              {data.policy_name || t('unknownSource')}
            </Typography.Title>
            <Typography.Paragraph className={dark ? '!mb-1 !text-[#d1d5db]' : '!mb-1 !text-[#4b5563]'}>
              {data.summary || t('extractionEmpty')}
            </Typography.Paragraph>
            <div className="flex flex-wrap gap-2 pt-2">
              {data.publish_time ? <Tag>{data.publish_time}</Tag> : null}
              {data.issuer ? <Tag>{data.issuer}</Tag> : null}
              {data.location ? <Tag>{data.location}</Tag> : null}
            </div>
          </section>

          <FieldSection dark={dark} title={t('extractionAudience')} items={data.eligible_audience} />
          <FieldSection dark={dark} title={t('extractionSupport')} items={data.support_items} />
          <FieldSection dark={dark} title={t('extractionProcess')} items={data.application_process} />
          <FieldSection dark={dark} title={t('extractionMaterials')} items={data.application_materials} />
          <FieldSection dark={dark} title={t('extractionDeadlines')} items={data.deadlines} />
          <FieldSection dark={dark} title={t('extractionAmounts')} items={data.amounts} />
          <FieldSection dark={dark} title={t('extractionContacts')} items={data.contact_points} />

          {data.source_url ? (
            <Button type="default" href={data.source_url} target="_blank" rel="noreferrer">
              {t('openSource')}
            </Button>
          ) : null}
        </div>
      ) : (
        <Typography.Paragraph className={dark ? '!text-[#9ca3af]' : '!text-[#6b7280]'}>
          {t('extractionEmpty')}
        </Typography.Paragraph>
      )}
    </Drawer>
  )
}

type FieldSectionProps = {
  dark: boolean
  title: string
  items: string[]
}

function FieldSection({ dark, title, items }: FieldSectionProps) {
  if (!items.length) {
    return null
  }

  return (
    <section>
      <Typography.Title level={5} className={dark ? '!mb-2 !text-[#f3f4f6]' : '!mb-2 !text-[#111827]'}>
        {title}
      </Typography.Title>
      <div className="space-y-2">
        {items.map((item) => (
          <div
            key={`${title}-${item}`}
            className={
              dark
                ? 'rounded-2xl border border-white/10 bg-white/6 px-3 py-2 text-sm text-[#d1d5db]'
                : 'rounded-2xl border border-black/6 bg-[#f7f7f8] px-3 py-2 text-sm text-[#374151]'
            }
          >
            {item}
          </div>
        ))}
      </div>
    </section>
  )
}
