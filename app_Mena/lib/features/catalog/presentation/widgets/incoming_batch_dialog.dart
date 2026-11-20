import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/dio_client.dart';
import '../../../../core/theme/app_colors.dart';
import '../../domain/models/product.dart';
import '../catalog_providers.dart';

class IncomingBatchDialog extends ConsumerStatefulWidget {
  const IncomingBatchDialog({
    required this.products,
    required this.storeId,
    super.key,
  });

  final List<Product> products;
  final int storeId;

  @override
  ConsumerState<IncomingBatchDialog> createState() => _IncomingBatchDialogState();
}

class _IncomingBatchDialogState extends ConsumerState<IncomingBatchDialog> {
  final _formKey = GlobalKey<FormState>();
  final _batchIdController = TextEditingController();
  final _quantityController = TextEditingController();

  Product? _selectedProduct;
  DateTime _selectedDate = DateTime.now().add(const Duration(days: 7));
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    if (widget.products.isNotEmpty) {
      _selectedProduct = widget.products.first;
    }
  }

  @override
  void dispose() {
    _batchIdController.dispose();
    _quantityController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate.isAfter(now) ? _selectedDate : now.add(const Duration(days: 1)),
      firstDate: now.add(const Duration(days: 1)),
      lastDate: now.add(const Duration(days: 365 * 2)),
    );
    if (picked != null) {
      setState(() => _selectedDate = picked);
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate() || _selectedProduct == null) {
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final dio = ref.read(dioProvider);
      final expirationDateStr =
          '${_selectedDate.year.toString().padLeft(4, '0')}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}';

      final response = await dio.post(
        '/batches/incoming',
        data: {
          'product_id': _selectedProduct!.id,
          'batch_id': _batchIdController.text.trim(),
          'quantity': int.parse(_quantityController.text.trim()),
          'expiration_date': expirationDateStr,
        },
      );

      if (!mounted) return;

      if (response.statusCode == 200 || response.statusCode == 201) {
        ref.invalidate(productsProvider);
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Batch ${_batchIdController.text.trim()} added. Product stock updated.',
            ),
            backgroundColor: AppColors.safe,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } on DioException catch (e) {
      if (!mounted) return;
      final msg = e.response?.data?['detail'] ?? e.message ?? 'Failed to add batch';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: $msg'),
          backgroundColor: AppColors.critical,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: $e'),
          backgroundColor: AppColors.critical,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Row(
        children: [
          Icon(Icons.local_shipping_rounded, color: AppColors.forestGreen),
          SizedBox(width: 8),
          Text('Receive Shipment', style: TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
      content: SizedBox(
        width: 400,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Select Product',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 4),
                DropdownButtonFormField<Product>(
                  initialValue: _selectedProduct,
                  isExpanded: true,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                  items: widget.products.map((p) {
                    return DropdownMenuItem<Product>(
                      value: p,
                      child: Text(
                        '${p.name} (${p.sku})',
                        overflow: TextOverflow.ellipsis,
                      ),
                    );
                  }).toList(),
                  onChanged: (p) => setState(() => _selectedProduct = p),
                  validator: (v) => v == null ? 'Please select a product' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _batchIdController,
                  decoration: const InputDecoration(
                    labelText: 'Batch ID / Code',
                    hintText: 'e.g., BATCH-2026-A1',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.qr_code_rounded),
                  ),
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) {
                      return 'Batch ID is required';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _quantityController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Shipment Units Received',
                    hintText: 'e.g., 20',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.numbers_rounded),
                  ),
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) {
                      return 'Quantity is required';
                    }
                    final n = int.tryParse(v.trim());
                    if (n == null || n <= 0) {
                      return 'Must be an integer greater than 0';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                InkWell(
                  onTap: _pickDate,
                  borderRadius: BorderRadius.circular(4),
                  child: InputDecorator(
                    decoration: const InputDecoration(
                      labelText: 'Expiration Date',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.calendar_today_rounded),
                    ),
                    child: Text(
                      '${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isSubmitting ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _isSubmitting ? null : _submit,
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.forestGreen,
            foregroundColor: Colors.white,
          ),
          child: _isSubmitting
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Text('Add Shipment'),
        ),
      ],
    );
  }
}
