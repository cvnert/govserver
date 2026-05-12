import { DownOutlined, EyeOutlined, PlusOutlined } from '@ant-design/icons'
import { Button, Collapse, Form, Input, Modal, Space, Switch, Typography } from 'antd'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import type { SourceCreateRequest, SourceDiscoverResponse } from '../../types/gov'

type SourceCreateModalProps = {
  open: boolean
  loading: boolean
  dark: boolean
  onClose: () => void
  onDiscover: (url: string) => Promise<SourceDiscoverResponse>
  onSubmit: (values: SourceCreateRequest) => Promise<void>
}

export function SourceCreateModal({
  open,
  loading,
  dark,
  onClose,
  onDiscover,
  onSubmit,
}: SourceCreateModalProps) {
  const { t } = useTranslation()
  const [form] = Form.useForm<SourceCreateRequest>()
  const [discovering, setDiscovering] = useState(false)
  const [discovery, setDiscovery] = useState<SourceDiscoverResponse | null>(null)
  const [discoverError, setDiscoverError] = useState('')

  return (
    <Modal
      open={open}
      title={t('addSource')}
      onCancel={onClose}
      footer={null}
      destroyOnHidden
      className={dark ? 'gov-modal gov-modal-dark' : 'gov-modal gov-modal-light'}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          enabled: true,
          crawler: 'generic_gov',
          key: '',
          base_url: '',
          channels: [
            {
              name: '',
              url: '',
              item_selector: '.cont_right_list li',
              link_selector: 'a',
              list_date_selector: '',
              issuer: '',
            },
          ],
        }}
        onFinish={async (values) => {
          await onSubmit(values)
          form.resetFields()
          setDiscovery(null)
          setDiscoverError('')
        }}
      >
        <Form.Item name="name" label={t('sourceName')} rules={[{ required: true }]}>
          <Input placeholder="杭州市人力资源和社会保障局" />
        </Form.Item>
        <Form.Item name="region" label={t('sourceRegion')}>
          <Input placeholder="浙江杭州" />
        </Form.Item>
        <Form.Item name="enabled" label={t('sourceEnabled')} valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.List name="channels">
          {(fields, { add, remove }) => (
            <div className="space-y-4">
              {fields.map((field, index) => (
                <div
                  key={field.key}
                  className={
                    dark
                      ? 'rounded-2xl border border-white/10 bg-white/5 p-4'
                      : 'rounded-2xl border border-black/8 bg-[#f7f7f8] p-4'
                  }
                >
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-sm font-medium">{t('sourceChannel')} {index + 1}</span>
                    {fields.length > 1 ? (
                      <Button type="text" danger onClick={() => remove(field.name)}>
                        {t('removeChannel')}
                      </Button>
                    ) : null}
                  </div>

                  <Form.Item name={[field.name, 'name']} label={t('channelName')} rules={[{ required: true }]}>
                    <Input placeholder="通知公告" />
                  </Form.Item>
                  <Form.Item name={[field.name, 'url']} label={t('channelUrl')} rules={[{ required: true }]}>
                    <Input placeholder="https://hrss.hangzhou.gov.cn/col/col1229113731/index.html" />
                  </Form.Item>

                  <div className="mb-4 flex flex-wrap gap-2">
                    <Button
                      icon={<EyeOutlined />}
                      loading={discovering}
                      onClick={async () => {
                        const url = form.getFieldValue(['channels', field.name, 'url'])
                        if (!url) {
                          return
                        }
                        setDiscovering(true)
                        setDiscoverError('')
                        try {
                          const result = await onDiscover(url)
                          const parsed = new URL(url)
                          setDiscovery(result)
                          form.setFieldValue('base_url', `${parsed.protocol}//${parsed.host}`)
                          form.setFieldValue(['channels', field.name, 'item_selector'], result.item_selector)
                          form.setFieldValue(['channels', field.name, 'link_selector'], result.link_selector)
                          form.setFieldValue(['channels', field.name, 'list_date_selector'], result.list_date_selector)
                        } catch (error) {
                          setDiscoverError(error instanceof Error ? error.message : t('requestFailed'))
                        } finally {
                          setDiscovering(false)
                        }
                      }}
                    >
                      {t('autoDiscover')}
                    </Button>
                  </div>

                  {discoverError ? <div className="mb-4 text-sm text-rose-500">{discoverError}</div> : null}

                  {discovery?.previews?.length ? (
                    <div className="mb-4 space-y-2">
                      <Typography.Text strong>{t('previewResult')}</Typography.Text>
                      {discovery.previews.map((item) => (
                        <div
                          key={item.url}
                          className={
                            dark
                              ? 'rounded-xl border border-white/10 bg-white/6 px-3 py-2 text-sm text-[#d1d5db]'
                              : 'rounded-xl border border-black/6 bg-white px-3 py-2 text-sm text-[#374151]'
                          }
                        >
                          <div>{item.title}</div>
                          {item.publish_time ? <div className="mt-1 text-xs opacity-70">{item.publish_time}</div> : null}
                        </div>
                      ))}
                    </div>
                  ) : null}

                  <Collapse
                    ghost
                    expandIcon={({ isActive }) => <DownOutlined rotate={isActive ? 180 : 0} />}
                    items={[
                      {
                        key: 'advanced',
                        label: t('advancedMode'),
                        children: (
                          <div>
                            <Form.Item name="base_url" label={t('sourceBaseUrl')}>
                              <Input placeholder="https://hrss.hangzhou.gov.cn" />
                            </Form.Item>
                            <Form.Item name="key" label={t('sourceKey')}>
                              <Input placeholder="自动生成，可选手动覆盖" />
                            </Form.Item>
                            <Form.Item name={[field.name, 'item_selector']} label={t('itemSelector')} rules={[{ required: true }]}>
                              <Input placeholder=".cont_right_list li" />
                            </Form.Item>
                            <Space.Compact block>
                              <Form.Item className="w-full" name={[field.name, 'link_selector']} label={t('linkSelector')} rules={[{ required: true }]}>
                                <Input placeholder="a" />
                              </Form.Item>
                              <Form.Item className="w-full" name={[field.name, 'list_date_selector']} label={t('dateSelector')}>
                                <Input placeholder="span" />
                              </Form.Item>
                            </Space.Compact>
                            <Form.Item name={[field.name, 'issuer']} label={t('channelIssuer')}>
                              <Input placeholder="杭州市人力资源和社会保障局" />
                            </Form.Item>
                          </div>
                        ),
                      },
                    ]}
                  />
                </div>
              ))}
              <Button icon={<PlusOutlined />} onClick={() => add()}>
                {t('addChannel')}
              </Button>
            </div>
          )}
        </Form.List>

        <div className="mt-6 flex justify-end gap-2">
          <Button onClick={onClose}>{t('cancel')}</Button>
          <Button type="primary" htmlType="submit" loading={loading}>
            {t('saveSource')}
          </Button>
        </div>
      </Form>
    </Modal>
  )
}
